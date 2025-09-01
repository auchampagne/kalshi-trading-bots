from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import time
import json
from tennis_data import TennisDataClient, TennisMatch
from kalshi_client import KalshiClient, MarketQuote, Environment
from model import fair_price_match_cents
from updater import ServeModel, ServePriors
from config import (
    SPORTSCORE_API_KEY,
    KALSHI_KEY_ID,
    KALSHI_KEY_FILE,
    MIN_EDGE_CENTS,
    EXCHANGE_FEES_CENTS,
    MAX_CONTRACTS,
    KELLY_FRACTION
)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

@dataclass
class ArbitrageOpportunity:
    market_id: str
    fair_price: float
    market_price: float
    edge: float
    recommended_size: int
    action: str  # "BUY" or "SELL"
    match_details: TennisMatch

class TennisArbitrageFinder:
    def __init__(self):
        # Initialize tennis data client
        self.tennis_client = TennisDataClient(SPORTSCORE_API_KEY)
        
        # Initialize Kalshi client
        private_key = self._load_private_key(KALSHI_KEY_FILE)
        self.kalshi_client = KalshiClient(KALSHI_KEY_ID, private_key, Environment.DEMO)
        
        # Initialize serve model
        self.serve_model = ServeModel(ServePriors())
        
        # Cache for tennis matches
        self.match_cache = {}
        
    def _load_private_key(self, key_file: str):
        with open(key_file, "rb") as f:
            return serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )

    def find_opportunities(self) -> List[ArbitrageOpportunity]:
        """Find arbitrage opportunities between live tennis matches and Kalshi markets."""
        opportunities = []
        
        # Get live tennis matches
        live_matches = self.tennis_client.get_live_matches()
        print(f"Found {len(live_matches)} live tennis matches")
        
        # Get available tennis markets from Kalshi
        tennis_markets = self.kalshi_client.find_tennis_markets()
        print(f"Found {len(tennis_markets)} tennis markets on Kalshi")
        
        # Update serve model with new match data
        self._update_serve_models(live_matches)
        
        # Look for matching markets and calculate edges
        for match in live_matches:
            for market in tennis_markets:
                if self._is_matching_market(match, market):
                    opp = self._analyze_opportunity(match, market)
                    if opp:
                        opportunities.append(opp)
        
        return opportunities

    def _update_serve_models(self, matches: List[TennisMatch]):
        """Update serve models with new match data."""
        for match in matches:
            match_id = f"{match.home_player}_{match.away_player}"
            
            # If we haven't seen this match before, create new entry
            if match_id not in self.match_cache:
                self.match_cache[match_id] = {
                    'last_game_score': (match.current_set_home_games, match.current_set_away_games),
                    'server': match.server
                }
                continue
            
            cached = self.match_cache[match_id]
            current_score = (match.current_set_home_games, match.current_set_away_games)
            
            # If the game score changed, update serve statistics
            if current_score != cached['last_game_score']:
                points_won = 4  # Assumption for clean game
                if cached['server'] == 'home':
                    self.serve_model.update_after_service_game(
                        'A',
                        points_won if current_score[0] > cached['last_game_score'][0] else 0,
                        4
                    )
                else:
                    self.serve_model.update_after_service_game(
                        'B',
                        points_won if current_score[1] > cached['last_game_score'][1] else 0,
                        4
                    )
                
                # Update cache
                self.match_cache[match_id] = {
                    'last_game_score': current_score,
                    'server': match.server
                }

    def _is_matching_market(self, match: TennisMatch, market: Dict) -> bool:
        """Check if a Kalshi market corresponds to a live match."""
        # This is a simplified match - you'll need to implement proper name matching
        market_title = market.get('title', '').lower()
        return (match.home_player.lower() in market_title and 
                match.away_player.lower() in market_title)

    def _analyze_opportunity(self, match: TennisMatch, market: Dict) -> Optional[ArbitrageOpportunity]:
        """Analyze a potential arbitrage opportunity."""
        try:
            # Get current market quote
            quote = self.kalshi_client.get_market_quote(market['id'])
            if not quote.best_bid_price or not quote.best_ask_price:
                return None
            
            # Calculate fair price using our model
            fair_price = fair_price_match_cents(
                state=self._convert_to_match_state(match),
                pA_serve=self.serve_model.current_pA(),
                pB_serve=self.serve_model.current_pB()
            )
            
            # Check for opportunities
            bid_edge = fair_price - quote.best_bid_price
            ask_edge = quote.best_ask_price - fair_price
            
            # Factor in exchange fees
            min_required_edge = MIN_EDGE_CENTS + EXCHANGE_FEES_CENTS
            
            if bid_edge > min_required_edge:
                # Opportunity to sell at the bid
                size = self._calculate_position_size(fair_price, quote.best_bid_price)
                return ArbitrageOpportunity(
                    market_id=market['id'],
                    fair_price=fair_price,
                    market_price=quote.best_bid_price,
                    edge=bid_edge,
                    recommended_size=size,
                    action="SELL",
                    match_details=match
                )
            elif ask_edge > min_required_edge:
                # Opportunity to buy at the ask
                size = self._calculate_position_size(fair_price, quote.best_ask_price)
                return ArbitrageOpportunity(
                    market_id=market['id'],
                    fair_price=fair_price,
                    market_price=quote.best_ask_price,
                    edge=ask_edge,
                    recommended_size=size,
                    action="BUY",
                    match_details=match
                )
            
        except Exception as e:
            print(f"Error analyzing opportunity: {e}")
        
        return None

    def _calculate_position_size(self, fair_price: float, market_price: float) -> int:
        """Calculate position size using Kelly criterion."""
        p = fair_price / 100.0
        q = 1.0 - p
        b = (100.0 - market_price) / market_price
        
        kelly = (p * (b + 1) - q) / b if b > 0 else 0
        kelly = max(0.0, min(1.0, kelly)) * KELLY_FRACTION
        
        # Get current balance
        balance = self.kalshi_client.get_balance()
        
        # Calculate maximum position size
        max_size = min(
            int(balance * kelly / market_price),
            MAX_CONTRACTS
        )
        
        return max_size

    def _convert_to_match_state(self, match: TennisMatch) -> 'MatchState':
        """Convert TennisMatch to MatchState for the model."""
        from state import MatchState
        return MatchState(
            set_games_a=match.current_set_home_games,
            set_games_b=match.current_set_away_games,
            sets_a=match.home_sets,
            sets_b=match.away_sets,
            pts_a=match.home_points,
            pts_b=match.away_points,
            tiebreak=match.is_tiebreak,
            server='A' if match.server == 'home' else 'B'
        )
