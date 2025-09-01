from typing import Dict, Optional, List
from datetime import datetime
import logging
from crypto_api import CryptoDataClient, CryptoPrice
from market_analyzer import MarketAnalyzer, MarketSignal
from kalshi_client import KalshiClient, Environment
from config import (
    CRYPTO_API_KEYS,
    KALSHI_KEY_ID,
    KALSHI_KEY_FILE,
    MIN_EDGE_PERCENTAGE,
    MAX_RISK_PERCENTAGE,
    SCAN_INTERVAL_SECONDS
)

class CryptoArbitrageBot:
    """Main bot class for crypto arbitrage on Kalshi"""
    
    def __init__(self):
        self.setup_logging()
        self.crypto_client = CryptoDataClient(CRYPTO_API_KEYS)
        self.market_analyzer = MarketAnalyzer(MIN_EDGE_PERCENTAGE)
        self.kalshi_client = self.setup_kalshi_client()
        self.active_positions: Dict[str, Dict] = {}
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('crypto_arbitrage.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('crypto_arbitrage')
        
    def setup_kalshi_client(self) -> KalshiClient:
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
                environment=Environment.DEMO  # Change to PROD for live trading
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Kalshi client: {e}")
            raise
            
    def get_crypto_markets(self) -> List[Dict]:
        """Get all available crypto markets from Kalshi"""
        try:
            markets = self.kalshi_client.search_markets(series_ticker='CRYPTO')
            return [m for m in markets if m['status'] == 'active']
        except Exception as e:
            self.logger.error(f"Failed to fetch crypto markets: {e}")
            return []
            
    def execute_trade(self, signal: MarketSignal, bankroll: float):
        """Execute a trade based on the market signal"""
        try:
            position_size = self.market_analyzer.calculate_position_size(
                signal, bankroll, MAX_RISK_PERCENTAGE
            )
            
            # Place order
            order_result = self.kalshi_client.place_order(
                market_id=signal.market_id,
                side=signal.action.upper(),
                size=int(position_size),
                price=signal.price_target
            )
            
            self.logger.info(f"Placed order: {order_result}")
            self.active_positions[signal.market_id] = {
                'signal': signal,
                'order': order_result
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute trade: {e}")
            
    def run(self):
        """Main bot loop"""
        self.logger.info("Starting Crypto Arbitrage Bot...")
        
        while True:
            try:
                # Get current portfolio and bankroll
                portfolio = self.kalshi_client.get_portfolio()
                bankroll = float(portfolio.get('balance', 0))
                
                # Get all crypto markets
                markets = self.get_crypto_markets()
                
                for market in markets:
                    # Get current prices from exchanges
                    prices = self.crypto_client.get_eth_price()
                    
                    # Get Kalshi market price
                    kalshi_price = float(market.get('last_price', 0))
                    
                    # Analyze for opportunities
                    signal = self.market_analyzer.analyze_crypto_market(
                        prices, kalshi_price, market['id']
                    )
                    
                    if signal:
                        self.logger.info(f"Found opportunity: {signal}")
                        self.execute_trade(signal, bankroll)
                        
                time.sleep(SCAN_INTERVAL_SECONDS)
                
            except KeyboardInterrupt:
                self.logger.info("Shutting down bot...")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(SCAN_INTERVAL_SECONDS)
                
if __name__ == "__main__":
    bot = CryptoArbitrageBot()
    bot.run()
