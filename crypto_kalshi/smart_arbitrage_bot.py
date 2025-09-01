from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import logging
import time
from crypto_api import CryptoDataClient, CryptoPrice
from market_analyzer import MarketAnalyzer, MarketSignal
from strategy import TradingStrategy, PricePattern
from kalshi_client import KalshiClient, Environment
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from config import (
    CRYPTO_API_KEYS,
    KALSHI_KEY_ID,
    KALSHI_KEY_FILE,
    MIN_EDGE_PERCENTAGE,
    MAX_RISK_PERCENTAGE,
    SCAN_INTERVAL_SECONDS,
    ORDER_BOOK_DEPTH
)

class SmartArbitrageBot:
    """Enhanced crypto arbitrage bot with advanced trading strategies"""
    
    def __init__(self):
        self.setup_logging()
        self.crypto_client = CryptoDataClient(CRYPTO_API_KEYS)
        self.market_analyzer = MarketAnalyzer(MIN_EDGE_PERCENTAGE)
        self.trading_strategy = TradingStrategy()
        self.kalshi_client = self.setup_kalshi_client()
        self.active_orders: Dict[str, Dict] = {}
        self.order_history: Dict[str, List[Dict]] = {}
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('smart_arbitrage.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('smart_arbitrage')
        
    def setup_kalshi_client(self) -> KalshiClient:
        """Initialize Kalshi client with authentication"""
        try:
            with open(KALSHI_KEY_FILE, 'rb') as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
            return KalshiClient(
                key_id=KALSHI_KEY_ID,
                private_key=private_key,
                environment=Environment.DEMO
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Kalshi client: {e}")
            raise

    def get_order_book_imbalance(self, market_id: str) -> float:
        """Calculate order book imbalance ratio"""
        try:
            order_book = self.kalshi_client.get_order_book(
                market_id, depth=ORDER_BOOK_DEPTH
            )
            
            bid_volume = sum(float(bid['size']) for bid in order_book['bids'])
            ask_volume = sum(float(ask['size']) for ask in order_book['asks'])
            
            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                return 0.0
                
            return (bid_volume - ask_volume) / total_volume
            
        except Exception as e:
            self.logger.error(f"Error getting order book: {e}")
            return 0.0

    def manage_existing_orders(self, market_id: str, current_price: float):
        """Smart order management"""
        if market_id not in self.active_orders:
            return
            
        for order_id, order_info in self.active_orders[market_id].items():
            order_age = datetime.now() - order_info['timestamp']
            price_movement = (current_price - order_info['price']) / order_info['price']
            volatility = self.trading_strategy.calculate_volatility(
                self.trading_strategy.price_history.get(market_id, [])
            )
            
            if self.trading_strategy.should_cancel_order(
                order_age, price_movement, volatility
            ):
                try:
                    self.kalshi_client.cancel_order(market_id, order_id)
                    self.logger.info(f"Cancelled order {order_id} due to market conditions")
                    self.order_history[market_id].append({
                        'order_id': order_id,
                        'action': 'cancel',
                        'reason': 'market_conditions',
                        'timestamp': datetime.now()
                    })
                    del self.active_orders[market_id][order_id]
                except Exception as e:
                    self.logger.error(f"Error cancelling order: {e}")

    def execute_smart_trade(self, signal: MarketSignal, pattern: Optional[PricePattern]):
        """Execute trade with smart order pricing"""
        try:
            # Calculate order book imbalance
            imbalance = self.get_order_book_imbalance(signal.market_id)
            
            # Get current volatility
            volatility = self.trading_strategy.calculate_volatility(
                self.trading_strategy.price_history.get(signal.market_id, [])
            )
            
            # Calculate optimal order price
            optimal_price = self.trading_strategy.calculate_smart_order_price(
                signal.price_target,
                pattern,
                volatility,
                imbalance
            )
            
            # Place the order
            order_result = self.kalshi_client.place_order(
                market_id=signal.market_id,
                side=signal.action.upper(),
                size=int(signal.size),
                price=optimal_price
            )
            
            # Track the order
            if signal.market_id not in self.active_orders:
                self.active_orders[signal.market_id] = {}
            if signal.market_id not in self.order_history:
                self.order_history[signal.market_id] = []
                
            self.active_orders[signal.market_id][order_result['order_id']] = {
                'price': optimal_price,
                'timestamp': datetime.now(),
                'signal': signal,
                'pattern': pattern
            }
            
            self.order_history[signal.market_id].append({
                'order_id': order_result['order_id'],
                'action': 'place',
                'price': optimal_price,
                'timestamp': datetime.now()
            })
            
            self.logger.info(
                f"Placed smart order: {order_result['order_id']} at {optimal_price}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to execute smart trade: {e}")

    def run(self):
        """Main bot loop with enhanced trading logic"""
        self.logger.info("Starting Smart Crypto Arbitrage Bot...")
        
        while True:
            try:
                # Get current portfolio and bankroll
                portfolio = self.kalshi_client.get_portfolio()
                bankroll = float(portfolio.get('balance', 0))
                
                # Get all crypto markets
                markets = self.kalshi_client.search_markets(series_ticker='CRYPTO')
                
                for market in markets:
                    if market['status'] != 'active':
                        continue
                        
                    # Get current prices from exchanges
                    prices = self.crypto_client.get_eth_price()
                    if not prices:
                        continue
                        
                    # Update price history for pattern recognition
                    avg_price = sum(p.price for p in prices) / len(prices)
                    self.trading_strategy.update_price_history(
                        market['id'], avg_price
                    )
                    
                    # Detect price patterns
                    pattern = self.trading_strategy.detect_price_patterns(market['id'])
                    
                    # Manage existing orders
                    self.manage_existing_orders(market['id'], avg_price)
                    
                    # Analyze for opportunities
                    signal = self.market_analyzer.analyze_crypto_market(
                        prices, float(market['last_price']), market['id']
                    )
                    
                    if signal:
                        self.logger.info(
                            f"Found opportunity: {signal}, Pattern: {pattern}"
                        )
                        self.execute_smart_trade(signal, pattern)
                        
                time.sleep(SCAN_INTERVAL_SECONDS)
                
            except KeyboardInterrupt:
                self.logger.info("Shutting down bot...")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(SCAN_INTERVAL_SECONDS)

if __name__ == "__main__":
    bot = SmartArbitrageBot()
    bot.run()
