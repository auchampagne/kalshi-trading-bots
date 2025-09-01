from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
import numpy as np
from crypto_api import CryptoPrice

@dataclass
class MarketSignal:
    symbol: str
    action: str  # 'buy' or 'sell'
    confidence: float
    price_target: float
    timestamp: datetime
    market_id: str
    exchange_prices: List[CryptoPrice]

class MarketAnalyzer:
    """Analyzes crypto market data and generates trading signals"""
    
    def __init__(self, min_edge_percentage: float = 0.5):
        self.min_edge_percentage = min_edge_percentage
        
    def analyze_crypto_market(self, prices: List[CryptoPrice], kalshi_price: float, 
                            market_id: str) -> Optional[MarketSignal]:
        """
        Analyze price differences between exchanges and Kalshi markets
        Returns a trading signal if an opportunity is found
        """
        if not prices:
            return None
            
        # Calculate average price across exchanges
        exchange_prices = [p.price for p in prices]
        avg_price = np.mean(exchange_prices)
        std_dev = np.std(exchange_prices)
        
        # Calculate edge percentage
        edge_percentage = abs((kalshi_price - avg_price) / avg_price) * 100
        
        if edge_percentage > self.min_edge_percentage:
            confidence = min(edge_percentage / (2 * self.min_edge_percentage), 1.0)
            action = 'buy' if kalshi_price < avg_price else 'sell'
            
            return MarketSignal(
                symbol='ETH',
                action=action,
                confidence=confidence,
                price_target=avg_price,
                timestamp=datetime.now(),
                market_id=market_id,
                exchange_prices=prices
            )
            
        return None

    def calculate_position_size(self, signal: MarketSignal, bankroll: float, 
                              max_risk_percentage: float = 2.0) -> float:
        """Calculate position size based on confidence and bankroll"""
        max_position = bankroll * (max_risk_percentage / 100)
        return max_position * signal.confidence
