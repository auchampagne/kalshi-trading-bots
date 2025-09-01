import os
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from tennis_data import TennisDataClient
from tennis_probability import TennisProbabilityModel
from kalshi_tennis import KalshiTennisTrader
from kalshi_auth import load_private_key_from_file
from kalshi_client import KalshiClient, Environment

class TennisTradingBot:
    def __init__(self):
        # Initialize logging
        self.setup_logging()
        
        # Load configuration
        self.load_config()
        
        # Initialize components
        self.setup_clients()
        
        # Trading parameters
        self.min_edge = Decimal(os.getenv('MIN_EDGE_CENTS', '2.0'))
        self.max_position = int(os.getenv('MAX_CONTRACTS', '10'))
        self.kelly_fraction = float(os.getenv('KELLY_FRACTION', '0.25'))
        self.exchange_fees = Decimal(os.getenv('EXCHANGE_FEES_CENTS', '1.5'))
        
        # Track positions and opportunities
        self.active_positions: Dict[str, Dict] = {}
        self.tracked_opportunities: Dict[str, Dict] = {}
        
    def setup_logging(self):
        """Configure logging for the bot."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('tennis_trading.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('TennisTradingBot')
        
    def load_config(self):
        """Load configuration from environment variables."""
        required_vars = [
            'SPORTSCORE_API_KEY',
            'KALSHI_KEY_ID',
            'KALSHI_KEY_FILE',
            'KALSHI_DEMO_MODE'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
            
        self.demo_mode = os.getenv('KALSHI_DEMO_MODE', 'True').lower() == 'true'
        
    def setup_clients(self):
        """Initialize API clients and models."""
        # Tennis data client
        self.tennis_client = TennisDataClient(os.getenv('SPORTSCORE_API_KEY'))
        
        # Probability model
        self.prob_model = TennisProbabilityModel()
        
        # Kalshi client
        private_key = load_private_key_from_file(os.getenv('KALSHI_KEY_FILE'))
        environment = Environment.DEMO if self.demo_mode else Environment.PROD
        self.kalshi_client = KalshiClient(
            key_id=os.getenv('KALSHI_KEY_ID'),
            private_key=private_key,
            environment=environment
        )
        
        # Tennis trader
        self.tennis_trader = KalshiTennisTrader(self.kalshi_client, self.prob_model)
        
    def update_player_stats(self, matches: List[Dict]):
        """Update player statistics based on recent matches."""
        for match in matches:
            if match.get('status') == 'completed':
                self.prob_model.update_player_stats([match], match['home_player'])
                self.prob_model.update_player_stats([match], match['away_player'])
                
    def find_opportunities(self) -> List[Dict]:
        """Find trading opportunities by comparing model prices to market prices."""
        opportunities = []
        
        # Get live matches
        live_matches = self.tennis_client.get_live_matches()
        self.logger.info(f"Found {len(live_matches)} live matches")
        
        # Update player stats with recent matches
        recent_matches = self.tennis_client.search_tennis_events(
            date_start=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            status='completed'
        )
        self.update_player_stats(recent_matches)
        
        # Look for opportunities in each match
        for match in live_matches:
            # Search for corresponding markets
            markets = self.tennis_trader.search_tennis_markets(match.home_player)
            markets.extend(self.tennis_trader.search_tennis_markets(match.away_player))
            
            for market in markets:
                analysis = self.tennis_trader.analyze_tennis_market(
                    market_id=market['id'],
                    surface=match.surface,
                    best_of_five=match.best_of_five
                )
                
                if analysis.get('error'):
                    self.logger.warning(f"Error analyzing market {market['id']}: {analysis['error']}")
                    continue
                    
                # Calculate edge
                if analysis['recommended_side'] and analysis['kelly_fraction'] > 0:
                    edge = abs(analysis['model_probability'] * 100 - 
                             float(analysis['yes_price' if analysis['recommended_side'] == 'yes' 
                                   else analysis['no_price']]))
                    
                    if edge > float(self.min_edge + self.exchange_fees):
                        opportunities.append({
                            'market_id': market['id'],
                            'match_id': match.id,
                            'edge': edge,
                            'analysis': analysis
                        })
                        
        return opportunities
        
    def execute_trades(self, opportunities: List[Dict]):
        """Execute trades for identified opportunities."""
        for opp in opportunities:
            market_id = opp['market_id']
            analysis = opp['analysis']
            
            # Skip if we already have a position in this market
            if market_id in self.active_positions:
                continue
                
            try:
                # Place the trade
                trade_result = self.tennis_trader.place_tennis_trade(
                    market_id=market_id,
                    side=analysis['recommended_side'],
                    size=analysis['kelly_fraction']
                )
                
                if trade_result.get('error'):
                    self.logger.error(f"Trade error for {market_id}: {trade_result['error']}")
                    continue
                    
                # Log the trade
                self.logger.info(
                    f"Trade placed for {market_id}:\n"
                    f"Side: {analysis['recommended_side']}\n"
                    f"Size: {analysis['kelly_fraction']}\n"
                    f"Edge: {opp['edge']:.2f} cents\n"
                    f"Model prob: {analysis['model_probability']:.2%}"
                )
                
                # Track the position
                self.active_positions[market_id] = {
                    'entry_time': datetime.now(),
                    'side': analysis['recommended_side'],
                    'size': analysis['kelly_fraction'],
                    'entry_price': analysis['yes_price' if analysis['recommended_side'] == 'yes' 
                                 else analysis['no_price']]
                }
                
            except Exception as e:
                self.logger.error(f"Error executing trade for {market_id}: {str(e)}")
                
    def manage_positions(self):
        """Monitor and manage existing positions."""
        for market_id, position in list(self.active_positions.items()):
            try:
                # Get current market state
                market = self.tennis_trader.get_market_details(market_id)
                
                # Skip if market is closed
                if market['status'] != 'active':
                    self.logger.info(f"Market {market_id} closed. Final outcome: {market['result']}")
                    del self.active_positions[market_id]
                    continue
                    
                # Check for exit conditions (you can add more sophisticated exit logic here)
                current_price = (Decimal(market['yes_bid']) if position['side'] == 'yes' 
                               else Decimal(market['no_bid']))
                entry_price = Decimal(position['entry_price'])
                
                # Example: Exit if price moves significantly against us
                if ((position['side'] == 'yes' and current_price < entry_price * Decimal('0.7')) or
                    (position['side'] == 'no' and current_price < entry_price * Decimal('0.7'))):
                    
                    # Place exit order
                    self.tennis_trader.place_tennis_trade(
                        market_id=market_id,
                        side='no' if position['side'] == 'yes' else 'yes',
                        size=position['size']
                    )
                    
                    self.logger.info(f"Closed position in {market_id} due to adverse price movement")
                    del self.active_positions[market_id]
                    
            except Exception as e:
                self.logger.error(f"Error managing position for {market_id}: {str(e)}")
                
    def run(self):
        """Main bot loop."""
        self.logger.info("Starting tennis trading bot...")
        self.logger.info(f"Mode: {'Demo' if self.demo_mode else 'Production'}")
        
        while True:
            try:
                # Find opportunities
                opportunities = self.find_opportunities()
                self.logger.info(f"Found {len(opportunities)} potential opportunities")
                
                # Execute trades for new opportunities
                self.execute_trades(opportunities)
                
                # Manage existing positions
                self.manage_positions()
                
                # Wait before next iteration
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)  # Wait before retrying
                
if __name__ == "__main__":
    bot = TennisTradingBot()
    bot.run()
