import os
import time
import logging
from typing import Dict, List
from decimal import Decimal

from tennis_data import TennisMatch, search_tennis_events
from tennis_probability import TennisProbabilityModel
from kalshi_tennis import KalshiTennisTrader
from kalshi_api import KalshiAPI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tennis_trading.log'),
        logging.StreamHandler()
    ]
)

def setup_kalshi_client() -> KalshiAPI:
    """Initialize Kalshi API client with credentials."""
    email = os.getenv('KALSHI_EMAIL')
    password = os.getenv('KALSHI_PASSWORD')
    key_id = os.getenv('KALSHI_KEY_ID')
    private_key = os.getenv('KALSHI_PRIVATE_KEY')
    
    if not all([email, password, key_id, private_key]):
        raise ValueError("Missing Kalshi credentials in environment")
    
    return KalshiAPI(
        email=email,
        password=password,
        key_id=key_id,
        private_key=private_key
    )

def main():
    # Initialize components
    kalshi_client = setup_kalshi_client()
    probability_model = TennisProbabilityModel()
    trader = KalshiTennisTrader(kalshi_client, probability_model)
    
    # Track processed markets to avoid duplicates
    processed_markets = set()
    
    while True:
        try:
            # Get live tennis matches
            matches = search_tennis_events()
            
            for match in matches:
                # Search for corresponding Kalshi markets
                markets = trader.search_tennis_markets(match.home_player)
                markets.extend(trader.search_tennis_markets(match.away_player))
                
                for market in markets:
                    market_id = market['id']
                    
                    # Skip if we've already processed this market
                    if market_id in processed_markets:
                        continue
                    
                    # Analyze market for trading opportunity
                    analysis = trader.analyze_tennis_market(
                        market_id=market_id,
                        surface=match.surface,
                        best_of_five=match.best_of_five
                    )
                    
                    if analysis.get('error'):
                        logging.warning(f"Error analyzing market {market_id}: {analysis['error']}")
                        continue
                    
                    # Log analysis results
                    logging.info(f"Market Analysis: {analysis}")
                    
                    # If we have a recommended trade
                    if analysis['recommended_side'] and analysis['kelly_fraction'] > 0:
                        try:
                            # Place the trade
                            trade_result = trader.place_tennis_trade(
                                market_id=market_id,
                                side=analysis['recommended_side'],
                                size=analysis['kelly_fraction']
                            )
                            
                            if trade_result.get('error'):
                                logging.error(f"Trade error: {trade_result['error']}")
                            else:
                                logging.info(f"Trade placed successfully: {trade_result}")
                                
                        except Exception as e:
                            logging.error(f"Error placing trade: {str(e)}")
                    
                    # Mark market as processed
                    processed_markets.add(market_id)
            
            # Sleep to avoid hitting rate limits
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            logging.error(f"Main loop error: {str(e)}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    main()
