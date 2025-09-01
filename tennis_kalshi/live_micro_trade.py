#!/usr/bin/env python3
import os
import logging
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
from typing import Any, Dict, Optional, Tuple
import time
from kalshi_live_client import KalshiClient, Environment
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('tennis_live_trade')

class SmallTrader:
    """High-frequency limit order arbitrage strategy."""
    
    def __init__(self, client: KalshiClient):
        self.client = client
        self.max_position_value = Decimal('1.00')  # $1 max position
        self.min_trade_size = 1  # Minimum contracts
        self.max_trade_size = 10  # Maximum contracts per trade
        self.min_edge_cents = Decimal('0.5')  # Minimum edge to trade
        self.limit_spreads = [1, 2, 3]  # Limit order spreads in cents
        self.active_orders = {}  # Track active limit orders
        self.total_trades = 0
        self.total_profit_cents = Decimal('0')
        
    def place_limit_orders(self, market_id: str, yes_price: Decimal, no_price: Decimal) -> list:
        """Place multiple limit orders at different price levels."""
        orders = []
        
        for spread in self.limit_spreads:
            # YES side - buy lower, sell higher
            buy_price = yes_price - spread
            sell_price = yes_price + spread
            if buy_price > 0 and sell_price < 100:
                buy_order = self.place_micro_trade(market_id, 'yes', buy_price, True)
                sell_order = self.place_micro_trade(market_id, 'no', sell_price, True)
                orders.extend([buy_order, sell_order])
            
            # NO side - buy lower, sell higher
            buy_price = no_price - spread
            sell_price = no_price + spread
            if buy_price > 0 and sell_price < 100:
                buy_order = self.place_micro_trade(market_id, 'no', buy_price, True)
                sell_order = self.place_micro_trade(market_id, 'yes', sell_price, True)
                orders.extend([buy_order, sell_order])
                
        return orders
        
    def cancel_old_orders(self):
        """Cancel orders that are too old or no longer profitable."""
        current_time = time.time()
        cancelled = []
        
        for order_id, order_info in list(self.active_orders.items()):
            if current_time - order_info['timestamp'] > 300:  # 5 minutes old
                try:
                    self.client.cancel_order(order_id)
                    cancelled.append(order_id)
                    del self.active_orders[order_id]
                except Exception as e:
                    logger.error(f"Failed to cancel order {order_id}: {e}")
                    
        return cancelled
        
    def get_bronzetti_gauff_market(self):
        """Get the specific market for Bronzetti vs Gauff."""
        markets = self.client.get_markets()
        
        # Find the specific market
        for market in markets:
            if "BRONZETTI" in market['title'].upper() and "GAUFF" in market['title'].upper():
                return market
        return None
        
    def calculate_position_size(self, price_cents: Decimal) -> int:
        """Calculate position size based on max position value."""
        max_contracts = int((self.max_position_value * 100) / price_cents)
        return min(max(self.min_trade_size, max_contracts), self.max_trade_size)
        
    def place_micro_trade(self, market_id: str, side: str, price_cents: Decimal, is_limit: bool = True) -> dict:
        """Place a small-sized trade."""
        size = self.calculate_position_size(price_cents)
        
        # Place the order
        order = self.client.create_order(
            market_id=market_id,
            side=side,
            price_cents=int(price_cents),
            size=size,
            order_type='limit' if is_limit else 'market'
        )
        
        order_info = {
            'order_id': order.get('order_id'),
            'side': side,
            'size': size,
            'price': float(price_cents),
            'total_cost': float(price_cents * Decimal(size)) / 100,
            'timestamp': time.time()
        }
        
        if is_limit:
            self.active_orders[order.get('order_id')] = order_info
            
        return order_info

def load_private_key() -> Any:
    """Load RSA private key from environment."""
    try:
        key_data = os.getenv('KALSHI_PRIVATE_KEY')
        if not key_data:
            raise ValueError("KALSHI_PRIVATE_KEY not found in environment")
            
        private_key = serialization.load_pem_private_key(
            key_data.encode(),
            password=None
        )
        return private_key
    except Exception as e:
        logger.error(f"Failed to load private key: {e}")
        raise

def find_arbitrage(market):
    """Find arbitrage opportunities in a market."""
    yes_bid = Decimal(market['yes_bid'] if market['yes_bid'] else '0')
    yes_ask = Decimal(market['yes_ask'] if market['yes_ask'] else '100')
    no_bid = Decimal(market['no_bid'] if market['no_bid'] else '0')
    no_ask = Decimal(market['no_ask'] if market['no_ask'] else '100')
    
    # Check for arbitrage opportunities
    arb1 = yes_bid + no_bid - 100  # Buy both sides
    arb2 = 100 - (yes_ask + no_ask)  # Sell both sides
    
    if arb1 > 0:
        return ('buy', arb1)
    elif arb2 > 0:
        return ('sell', arb2)
    return (None, 0)

def run_live_trading():
    """Run limit order arbitrage bot on Bronzetti vs Gauff match."""
    load_dotenv()
    
    logger.info("🎾 Tennis Limit Order Bot")
    logger.info("-" * 40)
    
    # Load Kalshi credentials
    key_id = "169ee023-6423-44fe-813e-0498d2369cfa"  # Using provided key
    
    try:
        # Initialize Kalshi client with provided private key
        with open('kalshi-key.pem', 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
            )
        
        client = KalshiClient(
            key_id=key_id,
            private_key=private_key,
            environment=Environment.DEMO  # Change to PROD for real trading
        )
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}")
        return
        
    try:
        # Initialize trader
        trader = SmallTrader(client)
        
        # Trading loop
        while True:
            # Get market
            market = trader.get_bronzetti_gauff_market()
            
            if not market:
                logger.info("Waiting for Bronzetti vs Gauff market...")
                time.sleep(30)
                continue
                
            logger.info(f"\nFound market: {market['title']}")
            logger.info(f"Current prices - Yes: {market['yes_bid']}/{market['yes_ask']}, No: {market['no_bid']}/{market['no_ask']}")
            
            # Check if match has started
            if market.get('status', 'active') != 'active':
                logger.info("Match has started, stopping bot.")
                break
                
            # Cancel old orders
            cancelled = trader.cancel_old_orders()
            if cancelled:
                logger.info(f"Cancelled {len(cancelled)} old orders")
                
            # Place new limit orders
            yes_price = Decimal(market['yes_bid'] if market['yes_bid'] else '50')
            no_price = Decimal(market['no_bid'] if market['no_bid'] else '50')
            
            orders = trader.place_limit_orders(market['id'], yes_price, no_price)
            
            # Log trading activity
            logger.info(f"✅ Placed {len(orders)} limit orders")
            logger.info(f"Active orders: {len(trader.active_orders)}")
            logger.info(f"Total trades: {trader.total_trades}")
            logger.info(f"Total profit: ${trader.total_profit_cents/100:.2f}")
            
            # Wait before next check
            time.sleep(15)
            
    except KeyboardInterrupt:
        logger.info("Stopping bot...")
        # Cancel all remaining orders
        trader.cancel_old_orders()
        logger.info("All orders cancelled")
    except Exception as e:
        logger.error(f"Error: {e}")
        # Try to cancel orders on error
        try:
            trader.cancel_old_orders()
        except Exception:
            pass

if __name__ == "__main__":
    run_live_trading()
