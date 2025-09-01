from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import re
from kalshi_api import KalshiAPI
from tennis_probability import TennisProbabilityModel

class KalshiTennisTrader:
    def __init__(self, kalshi_client: KalshiAPI, probability_model: TennisProbabilityModel):
        self.kalshi = kalshi_client
        self.model = probability_model
        self.kelly_fraction = 0.1  # Conservative Kelly criterion fraction
        
    def search_tennis_markets(self, player_name: str) -> List[Dict]:
        """Search for tennis markets related to a player."""
        # Use the search markets endpoint with tennis-specific parameters
        markets = self.kalshi.get_markets(
            series_ticker="TENNIS",  # Assuming this is the series ticker for tennis
            status="active",
            limit=100
        )
        
        # Filter for markets containing player name
        player_markets = []
        name_pattern = re.compile(player_name, re.IGNORECASE)
        
        for market in markets:
            if name_pattern.search(market.get('title', '')):
                player_markets.append(market)
                
        return player_markets
        
    def get_market_details(self, market_id: str) -> Dict:
        """Get detailed information about a specific market."""
        return self.kalshi.get_market(market_id)
        
    def extract_player_names(self, market_title: str) -> Tuple[str, str]:
        """Extract player names from market title."""
        # Example title format: "Djokovic vs Nadal - Wimbledon R3"
        # or "Will Djokovic defeat Nadal?"
        
        vs_pattern = re.compile(r"(.+?)\s+(?:vs\.?|versus)\s+(.+?)(?:\s+-|$)")
        will_pattern = re.compile(r"Will\s+(.+?)\s+defeat\s+(.+?)(?:\s+|$)")
        
        vs_match = vs_pattern.search(market_title)
        if vs_match:
            return vs_match.group(1).strip(), vs_match.group(2).strip()
            
        will_match = will_pattern.search(market_title)
        if will_match:
            return will_match.group(1).strip(), will_match.group(2).strip()
            
        return None, None
        
    def calculate_kelly_bet(self, 
                          probability: float, 
                          yes_price: Decimal, 
                          no_price: Decimal) -> Tuple[str, Decimal]:
        """Calculate optimal bet size using Kelly Criterion."""
        # Convert decimal prices to probabilities
        yes_implied_prob = 1 / float(yes_price)
        no_implied_prob = 1 / float(no_price)
        
        # Calculate Kelly fraction for both sides
        kelly_yes = (probability * float(yes_price) - 1) / float(yes_price)
        kelly_no = ((1 - probability) * float(no_price) - 1) / float(no_price)
        
        # Apply conservative fraction and determine which side to bet
        if kelly_yes > kelly_no and kelly_yes > 0:
            return "yes", Decimal(str(kelly_yes * self.kelly_fraction))
        elif kelly_no > 0:
            return "no", Decimal(str(kelly_no * self.kelly_fraction))
        
        return None, Decimal('0')
        
    def analyze_tennis_market(self, 
                            market_id: str, 
                            surface: str = 'hard',
                            best_of_five: bool = False) -> Dict:
        """Analyze a tennis market and determine if there's value."""
        market = self.get_market_details(market_id)
        
        # Extract player names
        player_a, player_b = self.extract_player_names(market['title'])
        if not player_a or not player_b:
            return {'error': 'Could not extract player names'}
            
        # Get current market prices
        yes_price = Decimal(market['yes_bid'])
        no_price = Decimal(market['no_bid'])
        
        # Calculate win probability using our model
        win_probability = self.model.calculate_match_win_probability(
            player_a_id=player_a,
            player_b_id=player_b,
            surface=surface,
            best_of_five=best_of_five
        )
        
        # Calculate Kelly bet
        side, size = self.calculate_kelly_bet(win_probability, yes_price, no_price)
        
        return {
            'market_id': market_id,
            'title': market['title'],
            'player_a': player_a,
            'player_b': player_b,
            'model_probability': win_probability,
            'yes_price': yes_price,
            'no_price': no_price,
            'recommended_side': side,
            'kelly_fraction': size,
            'surface': surface,
            'best_of_five': best_of_five
        }
        
    def place_tennis_trade(self, 
                          market_id: str, 
                          side: str, 
                          size: Decimal,
                          max_price: Optional[Decimal] = None) -> Dict:
        """Place a trade in a tennis market."""
        # Get current market state
        market = self.get_market_details(market_id)
        
        # Determine appropriate price limit
        if max_price is None:
            max_price = (Decimal(market['yes_ask']) 
                        if side == 'yes' else Decimal(market['no_ask']))
        
        # Calculate number of contracts based on available balance
        balance = Decimal(self.kalshi.get_balance()['balance'])
        max_contracts = int(balance * size)
        
        if max_contracts < 1:
            return {'error': 'Insufficient balance for trade'}
            
        # Place the order
        order = self.kalshi.create_order(
            market_id=market_id,
            side=side,
            order_type='limit',
            price=max_price,
            size=max_contracts
        )
        
        return order
