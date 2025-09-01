import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from decimal import Decimal

from tennis_probability import TennisProbabilityModel
from kalshi_demo_client import KalshiClient, Environment

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger('tennis_test')

def setup_demo_match():
    """Create a demo tennis match."""
    from tennis_data import TennisMatch
    return TennisMatch(
        id=1,
        home_player="Novak Djokovic",
        away_player="Rafael Nadal",
        surface="grass",
        best_of_five=True,
        status="active",
        tournament_name="Wimbledon Demo"
    )

def setup_kalshi_client() -> KalshiClient:
    """Initialize demo Kalshi client."""
    print("🔑 Setting up demo Kalshi client...")
    return KalshiClient(
        key_id="demo_key",
        private_key=None,
        environment=Environment.DEMO
    )

def demo_trade():
    """Run a demo trade."""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting tennis trading demo...")
    
    try:
        # Get demo match
        match = setup_demo_match()
        logger.info(f"\nAnalyzing match: {match.home_player} vs {match.away_player}")
        
        # Initialize probability model with demo data
        prob_model = TennisProbabilityModel()
        
        # Setup demo Kalshi client
        kalshi = setup_kalshi_client()
        
        # Get demo market
        market = kalshi.get_market("TENNIS-DEMO-1")
        
        # Calculate win probability (demo values)
        win_prob = 0.65  # 65% chance of player A winning
        
        # Calculate edge
        market_prob = float(market['yes_bid']) / 100.0
        edge = abs(win_prob - market_prob) * 100
        
        # Log analysis
        logger.info("\n📊 Market Analysis:")
        logger.info(f"Title: {market['title']}")
        logger.info(f"Model Probability: {win_prob:.2%}")
        logger.info(f"Market Probability: {market_prob:.2%}")
        logger.info(f"Edge: {edge:.2f} cents")
        logger.info(f"Yes Price: {market['yes_bid']}")
        logger.info(f"No Price: {market['no_bid']}")
        
        # Place demo trade
        logger.info("\n💫 Placing demo trade...")
        size = 10  # Demo size
        side = 'yes' if win_prob > market_prob else 'no'
        
        trade = kalshi.place_order(
            market_id=market['id'],
            side=side,
            size=size,
            price=float(market['yes_bid'] if side == 'yes' else market['no_bid'])
        )
        
        logger.info("✅ Demo trade placed successfully!")
        logger.info(f"Order ID: {trade['order_id']}")
        logger.info(f"Side: {trade['side']}")
        logger.info(f"Size: {trade['size']} contracts")
        logger.info(f"Price: {trade['price']} cents")
            
    except Exception as e:
        logger.error(f"Error in demo trade: {str(e)}")

if __name__ == "__main__":
    demo_trade()
