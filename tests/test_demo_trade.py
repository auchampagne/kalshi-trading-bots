import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from decimal import Decimal

from tennis_data import search_tennis_events, TennisMatch
from kalshi_tennis import KalshiTennisTrader
from tennis_probability import TennisProbabilityModel
from kalshi_client import KalshiClient, Environment
from kalshi_auth import load_private_key_from_file

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger('tennis_test')

def get_test_matches() -> List[TennisMatch]:
    """Get tennis matches for testing."""
    print("🔍 Fetching recent tennis matches...")
    
    # Get matches from last 7 days
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    return search_tennis_events(
        date_start=start_date,
        date_end=end_date,
        status='completed'
    )

def setup_kalshi_client() -> KalshiClient:
    """Initialize Kalshi client."""
    print("🔑 Setting up Kalshi client...")
    
    # Load private key
    key_file = os.getenv('KALSHI_KEY_FILE', 'kalshi-key.pem')
    private_key = load_private_key_from_file(key_file)
    
    # Create client
    return KalshiClient(
        key_id=os.getenv('KALSHI_KEY_ID', ''),
        private_key=private_key,
        environment=Environment.DEMO
    )

def demo_trade():
    """Run a demo trade."""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting tennis trading test...")
    
    try:
        # Get test matches
        matches = get_test_matches()
        if not matches:
            logger.error("No matches found for testing")
            return
            
        logger.info(f"Found {len(matches)} matches")
        
        # Initialize probability model
        prob_model = TennisProbabilityModel()
        
        # Update model with match data
        for match in matches:
            prob_model.update_player_stats([match], match.home_player)
            prob_model.update_player_stats([match], match.away_player)
            
        # Setup Kalshi client and trader
        kalshi = setup_kalshi_client()
        trader = KalshiTennisTrader(kalshi, prob_model)
        
        # Look for trading opportunities in first match
        test_match = matches[0]
        logger.info(f"\nAnalyzing match: {test_match.home_player} vs {test_match.away_player}")
        
        # Search for related markets
        markets = trader.search_tennis_markets(test_match.home_player)
        if not markets:
            logger.error("No Kalshi markets found for this match")
            return
            
        # Analyze first market
        market = markets[0]
        analysis = trader.analyze_tennis_market(
            market_id=market['id'],
            surface=test_match.surface,
            best_of_five=test_match.best_of_five
        )
        
        if analysis.get('error'):
            logger.error(f"Analysis error: {analysis['error']}")
            return
            
        # Log analysis
        logger.info("\nMarket Analysis:")
        logger.info(f"Title: {analysis['title']}")
        logger.info(f"Model Probability: {analysis['model_probability']:.2%}")
        logger.info(f"Yes Price: {analysis['yes_price']}")
        logger.info(f"No Price: {analysis['no_price']}")
        logger.info(f"Recommended Side: {analysis['recommended_side']}")
        logger.info(f"Kelly Fraction: {float(analysis['kelly_fraction']):.3f}")
        
        # Place demo trade if we have an edge
        if analysis['recommended_side'] and analysis['kelly_fraction'] > 0:
            logger.info("\n💫 Placing demo trade...")
            
            trade = trader.place_tennis_trade(
                market_id=market['id'],
                side=analysis['recommended_side'],
                size=analysis['kelly_fraction']
            )
            
            if trade.get('error'):
                logger.error(f"Trade error: {trade['error']}")
            else:
                logger.info("✅ Demo trade placed successfully!")
                logger.info(f"Order ID: {trade.get('order_id')}")
                logger.info(f"Size: {trade.get('size')} contracts")
                logger.info(f"Price: {trade.get('price')} cents")
        else:
            logger.info("\n⚠️ No trading edge found in this market")
            
    except Exception as e:
        logger.error(f"Error in demo trade: {str(e)}")

if __name__ == "__main__":
    demo_trade()
