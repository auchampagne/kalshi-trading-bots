import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
import os

# ---- Data Models ----

@dataclass
class TennisMatch:
    """Simple tennis match class for demo."""
    home_player: str
    away_player: str
    surface: str
    tournament: str

@dataclass
class MarketAnalysis:
    """Market analysis result."""
    market_id: str
    title: str
    win_probability: float
    yes_price: float
    no_price: float
    recommended_side: str
    size: int
    edge: float

# ---- Demo Kalshi Client ----

class KalshiDemo:
    """Demo Kalshi client that simulates trading."""
    
    def __init__(self):
        self.portfolio_balance = 10000  # $100.00
        
    def get_market(self, match: TennisMatch) -> Dict[str, Any]:
        """Get simulated market data."""
        return {
            'id': 'TENNIS-DEMO-1',
            'title': f"{match.home_player} vs {match.away_player} - {match.tournament}",
            'yes_price': 60,
            'no_price': 40,
            'status': 'active'
        }
        
    def analyze_market(self, match: TennisMatch) -> MarketAnalysis:
        """Analyze market and calculate edge."""
        market = self.get_market(match)
        
        # Demo probability calculation
        win_prob = 0.65 if match.surface == "grass" and match.home_player == "Novak Djokovic" else 0.55
        yes_price = float(market['yes_price'])
        no_price = float(market['no_price'])
        
        # Calculate edge
        edge = abs(win_prob - (yes_price / 100.0)) * 100
        
        # Determine position size (demo logic)
        size = 10 if edge > 3 else 5
        
        return MarketAnalysis(
            market_id=market['id'],
            title=market['title'],
            win_probability=win_prob,
            yes_price=yes_price,
            no_price=no_price,
            recommended_side="yes" if win_prob > (yes_price / 100.0) else "no",
            size=size,
            edge=edge
        )
        
    def place_trade(self, analysis: MarketAnalysis) -> Dict[str, Any]:
        """Simulate placing a trade."""
        price = analysis.yes_price if analysis.recommended_side == 'yes' else analysis.no_price
        cost = price * analysis.size
        
        # Simulate trade execution
        order_id = f"demo-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Update portfolio (demo)
        self.portfolio_balance -= cost
        
        return {
            'order_id': order_id,
            'market_id': analysis.market_id,
            'side': analysis.recommended_side,
            'size': analysis.size,
            'price': price,
            'cost': cost,
            'status': 'filled'
        }
        
    def get_portfolio(self) -> Dict[str, Any]:
        """Get portfolio status."""
        return {
            'balance': self.portfolio_balance,
            'buying_power': self.portfolio_balance
        }

# ---- Demo Trading Script ----

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger('tennis_demo')

def run_demo_trade():
    """Run a complete demo trade."""
    logger = setup_logging()
    logger.info("🎾 Tennis Trading Demo")
    logger.info("--------------------")
    
    try:
        # Create demo match
        match = TennisMatch(
            home_player="Novak Djokovic",
            away_player="Rafael Nadal",
            surface="grass",
            tournament="Wimbledon Demo"
        )
        
        logger.info(f"\n🎯 Analyzing Match:")
        logger.info(f"Players: {match.home_player} vs {match.away_player}")
        logger.info(f"Surface: {match.surface}")
        logger.info(f"Tournament: {match.tournament}")
        
        # Initialize demo client
        client = KalshiDemo()
        
        # Analyze market
        analysis = client.analyze_market(match)
        
        # Log analysis
        logger.info("\n📊 Market Analysis:")
        logger.info(f"Title: {analysis.title}")
        logger.info(f"Win Probability: {analysis.win_probability:.2%}")
        logger.info(f"Yes Price: {analysis.yes_price:.1f} cents")
        logger.info(f"No Price: {analysis.no_price:.1f} cents")
        logger.info(f"Edge: {analysis.edge:.2f} cents")
        logger.info(f"Recommended Side: {analysis.recommended_side}")
        logger.info(f"Recommended Size: {analysis.size} contracts")
        
        # Place demo trade
        logger.info("\n💫 Placing Trade...")
        trade = client.place_trade(analysis)
        
        # Log trade result
        logger.info("✅ Trade Executed:")
        logger.info(f"Order ID: {trade['order_id']}")
        logger.info(f"Side: {trade['side']}")
        logger.info(f"Size: {trade['size']} contracts")
        logger.info(f"Price: {trade['price']:.1f} cents")
        logger.info(f"Total Cost: ${trade['cost']/100:.2f}")
        
        # Show portfolio after trade
        portfolio = client.get_portfolio()
        logger.info("\n💰 Portfolio Status:")
        logger.info(f"Balance: ${portfolio['balance']/100:.2f}")
        logger.info(f"Buying Power: ${portfolio['buying_power']/100:.2f}")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    run_demo_trade()
