#!/usr/bin/env python3
import os
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Optional
from decimal import Decimal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('tennis_demo')

@dataclass
class TennisMatch:
    """Tennis match information."""
    player1: str
    player2: str
    surface: str
    tournament: str
    p1_stats: Dict[str, float]
    p2_stats: Dict[str, float]

class TennisProbability:
    """Tennis probability calculator."""
    
    @staticmethod
    def calculate_serve_hold_prob(stats: Dict[str, float]) -> float:
        """Calculate probability of holding serve based on stats."""
        first_serve_pct = stats.get('first_serve_pct', 0.62)
        first_serve_win_pct = stats.get('first_serve_win_pct', 0.72)
        second_serve_win_pct = stats.get('second_serve_win_pct', 0.52)
        
        return (first_serve_pct * first_serve_win_pct + 
                (1 - first_serve_pct) * second_serve_win_pct)
    
    @staticmethod
    def calculate_match_win_prob(p1_hold_prob: float, p2_hold_prob: float) -> float:
        """Calculate match win probability."""
        # Simplified model for demo
        total_hold_prob = p1_hold_prob + (1 - p2_hold_prob)
        return total_hold_prob / 2

class KalshiDemoTrader:
    """Demo implementation of Kalshi trading."""
    
    def __init__(self):
        self.balance = Decimal('10000')  # $100.00
    
    def get_market_price(self, match: TennisMatch) -> Dict[str, Decimal]:
        """Get simulated market prices."""
        # Demo market with some randomization based on player stats
        p1_hold = TennisProbability.calculate_serve_hold_prob(match.p1_stats)
        base_yes = Decimal(str(round(p1_hold * 100, 1)))
        return {
            'yes_bid': base_yes - Decimal('2'),
            'yes_ask': base_yes + Decimal('2'),
            'no_bid': Decimal('100') - base_yes - Decimal('2'),
            'no_ask': Decimal('100') - base_yes + Decimal('2')
        }
    
    def calculate_edge(self, fair_prob: float, market_price: Decimal) -> Decimal:
        """Calculate edge in cents."""
        fair_price = Decimal(str(fair_prob * 100))
        return abs(fair_price - market_price)
    
    def size_position(self, edge: Decimal, price: Decimal) -> int:
        """Calculate position size using Kelly Criterion."""
        kelly = float(edge) / 100.0  # Simple Kelly for demo
        bankroll = float(self.balance)
        max_risk = bankroll * 0.02  # Risk 2% max
        contracts = int(min(max_risk / float(price), 100))  # Max 100 contracts
        return max(1, int(contracts * kelly))
    
    def place_trade(self, match: TennisMatch) -> Dict:
        """Place a simulated trade."""
        # Calculate probabilities
        p1_hold = TennisProbability.calculate_serve_hold_prob(match.p1_stats)
        p2_hold = TennisProbability.calculate_serve_hold_prob(match.p2_stats)
        win_prob = TennisProbability.calculate_match_win_prob(p1_hold, p2_hold)
        
        # Get market prices
        prices = self.get_market_price(match)
        
        # Calculate edges
        yes_edge = self.calculate_edge(win_prob, prices['yes_bid'])
        no_edge = self.calculate_edge(1 - win_prob, prices['no_bid'])
        
        # Determine trade side
        if yes_edge > no_edge and yes_edge > Decimal('2'):
            side = 'yes'
            price = prices['yes_ask']
            edge = yes_edge
        elif no_edge > Decimal('2'):
            side = 'no'
            price = prices['no_ask']
            edge = no_edge
        else:
            return {'error': 'No sufficient edge found'}
        
        # Size the position
        size = self.size_position(edge, price)
        cost = size * price
        
        # Check if we can afford it
        if cost > self.balance:
            return {'error': 'Insufficient balance'}
        
        # Execute trade
        self.balance -= cost
        
        return {
            'match': f"{match.player1} vs {match.player2}",
            'tournament': match.tournament,
            'side': side,
            'size': size,
            'price': float(price),
            'edge': float(edge),
            'cost': float(cost),
            'remaining_balance': float(self.balance)
        }

def run_demo():
    """Run a complete trading demo."""
    logger.info("🎾 Tennis Trading Demo Started")
    logger.info("-" * 40)
    
    # Create demo match with realistic stats
    match = TennisMatch(
        player1="Novak Djokovic",
        player2="Rafael Nadal",
        surface="grass",
        tournament="Wimbledon",
        p1_stats={
            'first_serve_pct': 0.65,
            'first_serve_win_pct': 0.78,
            'second_serve_win_pct': 0.56
        },
        p2_stats={
            'first_serve_pct': 0.68,
            'first_serve_win_pct': 0.72,
            'second_serve_win_pct': 0.52
        }
    )
    
    logger.info(f"\n📊 Match Analysis:")
    logger.info(f"Match: {match.player1} vs {match.player2}")
    logger.info(f"Tournament: {match.tournament}")
    logger.info(f"Surface: {match.surface}")
    
    # Calculate serve hold probabilities
    p1_hold = TennisProbability.calculate_serve_hold_prob(match.p1_stats)
    p2_hold = TennisProbability.calculate_serve_hold_prob(match.p2_stats)
    
    logger.info(f"\n🎯 Serve Statistics:")
    logger.info(f"{match.player1} hold probability: {p1_hold:.1%}")
    logger.info(f"{match.player2} hold probability: {p2_hold:.1%}")
    
    # Initialize trader
    trader = KalshiDemoTrader()
    
    # Place trade
    logger.info("\n💫 Placing Trade...")
    result = trader.place_trade(match)
    
    if 'error' in result:
        logger.error(f"❌ Trade Error: {result['error']}")
    else:
        logger.info("✅ Trade Executed Successfully!")
        logger.info(f"Match: {result['match']}")
        logger.info(f"Side: {result['side'].upper()}")
        logger.info(f"Size: {result['size']} contracts")
        logger.info(f"Price: {result['price']:.1f} cents")
        logger.info(f"Edge: {result['edge']:.1f} cents")
        logger.info(f"Cost: ${result['cost']/100:.2f}")
        logger.info(f"Remaining Balance: ${result['remaining_balance']/100:.2f}")

if __name__ == "__main__":
    run_demo()
