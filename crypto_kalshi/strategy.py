from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from scipy import stats

@dataclass
class MarketTrend:
    direction: str  # 'up', 'down', 'sideways'
    strength: float  # 0 to 1
    duration: timedelta
    volatility: float

@dataclass
class PricePattern:
    pattern_type: str  # 'divergence', 'convergence', 'momentum'
    confidence: float
    timestamp: datetime
    price_points: List[float]

class TradingStrategy:
    def __init__(self, 
                 momentum_window: int = 20,
                 volatility_window: int = 30,
                 min_pattern_confidence: float = 0.7):
        self.momentum_window = momentum_window
        self.volatility_window = volatility_window
        self.min_pattern_confidence = min_pattern_confidence
        self.price_history: Dict[str, List[float]] = {}
        
    def update_price_history(self, symbol: str, price: float):
        """Update price history for pattern recognition"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(price)
        # Keep limited history
        self.price_history[symbol] = self.price_history[symbol][-1000:]

    def detect_momentum(self, prices: List[float]) -> float:
        """Calculate momentum indicator"""
        if len(prices) < self.momentum_window:
            return 0.0
            
        recent_prices = prices[-self.momentum_window:]
        return (recent_prices[-1] / recent_prices[0] - 1) * 100

    def calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility"""
        if len(prices) < self.volatility_window:
            return 0.0
            
        returns = np.diff(prices[-self.volatility_window:]) / prices[-self.volatility_window:-1]
        return np.std(returns) * np.sqrt(252)  # Annualized volatility

    def detect_price_patterns(self, symbol: str) -> Optional[PricePattern]:
        """Detect common price patterns"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 30:
            return None
            
        prices = self.price_history[symbol]
        
        # Detect price divergence from moving average
        sma = np.mean(prices[-20:])
        current_price = prices[-1]
        divergence = abs(current_price - sma) / sma
        
        # Detect momentum
        momentum = self.detect_momentum(prices)
        
        # Detect trend strength using linear regression
        x = np.arange(len(prices[-20:]))
        slope, _, r_value, _, _ = stats.linregress(x, prices[-20:])
        trend_strength = abs(r_value)
        
        if divergence > 0.02 and abs(momentum) > 1.0:  # 2% divergence and significant momentum
            pattern_type = 'divergence'
            confidence = min(divergence * 10, 1.0) * trend_strength
        elif trend_strength > 0.7:  # Strong trend
            pattern_type = 'momentum'
            confidence = trend_strength
        else:
            pattern_type = 'convergence'
            confidence = 1 - divergence
            
        if confidence >= self.min_pattern_confidence:
            return PricePattern(
                pattern_type=pattern_type,
                confidence=confidence,
                timestamp=datetime.now(),
                price_points=prices[-20:]
            )
            
        return None

    def should_cancel_order(self, order_age: timedelta, 
                          price_movement: float,
                          volatility: float) -> bool:
        """Determine if an existing order should be cancelled"""
        # Cancel if order is too old
        if order_age > timedelta(minutes=5):
            return True
            
        # Cancel if price has moved significantly
        if abs(price_movement) > volatility * 2:
            return True
            
        return False

    def calculate_smart_order_price(self, 
                                  market_price: float,
                                  pattern: Optional[PricePattern],
                                  volatility: float,
                                  order_book_imbalance: float) -> float:
        """Calculate optimal order price based on market conditions"""
        base_adjustment = 0.0
        
        # Adjust for pattern
        if pattern:
            if pattern.pattern_type == 'divergence':
                # Fade the divergence
                base_adjustment = -0.01 if market_price > pattern.price_points[-2] else 0.01
            elif pattern.pattern_type == 'momentum':
                # Follow the momentum
                base_adjustment = 0.01 if market_price > pattern.price_points[-2] else -0.01
                
        # Adjust for order book imbalance
        imbalance_adjustment = order_book_imbalance * 0.02
        
        # Adjust for volatility
        volatility_adjustment = volatility * 0.1
        
        total_adjustment = (base_adjustment + 
                          imbalance_adjustment + 
                          volatility_adjustment)
                          
        return market_price * (1 + total_adjustment)
