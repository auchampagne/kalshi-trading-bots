from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math
from tennis_data import TennisMatch

@dataclass
class PlayerStats:
    first_serve_pct: float = 0.62  # Default first serve percentage
    first_serve_win_pct: float = 0.72  # Default win % on first serve
    second_serve_win_pct: float = 0.50  # Default win % on second serve
    return_win_pct: float = 0.32  # Default return win percentage
    matches_analyzed: int = 0

class TennisProbabilityModel:
    def __init__(self):
        self.player_stats: Dict[str, PlayerStats] = {}
        self.surface_adjustments: Dict[str, float] = {
            'hard': 1.0,
            'clay': 0.95,  # Slightly favors better players
            'grass': 1.05,  # More variance due to serve advantage
            'indoor': 1.02  # Slightly favors big servers
        }
        
    def update_player_stats(self, matches: List[TennisMatch], player_id: str):
        """Update player statistics based on historical matches."""
        stats = PlayerStats()
        total_matches = 0
        
        for match in matches:
            is_home = match.home_player == player_id
            player_stats = match.home_stats if is_home else match.away_stats
            
            if not player_stats:
                continue
                
            # Update serve percentages
            if player_stats.get('first_serve_total', 0) > 0:
                first_serve_pct = player_stats.get('first_serve_made', 0) / player_stats.get('first_serve_total', 1)
                stats.first_serve_pct = ((stats.first_serve_pct * total_matches) + first_serve_pct) / (total_matches + 1)
            
            if player_stats.get('first_serve_made', 0) > 0:
                first_serve_win_pct = player_stats.get('first_serve_won', 0) / player_stats.get('first_serve_made', 1)
                stats.first_serve_win_pct = ((stats.first_serve_win_pct * total_matches) + first_serve_win_pct) / (total_matches + 1)
            
            if player_stats.get('second_serve_total', 0) > 0:
                second_serve_win_pct = player_stats.get('second_serve_won', 0) / player_stats.get('second_serve_total', 1)
                stats.second_serve_win_pct = ((stats.second_serve_win_pct * total_matches) + second_serve_win_pct) / (total_matches + 1)
            
            total_matches += 1
        
        stats.matches_analyzed = total_matches
        self.player_stats[player_id] = stats

    def calculate_serve_hold_probability(self, player_id: str, opponent_id: str, surface: str = 'hard') -> float:
        """Calculate probability of player holding their serve."""
        server = self.player_stats.get(player_id, PlayerStats())
        returner = self.player_stats.get(opponent_id, PlayerStats())
        
        # Calculate point win probabilities on serve
        first_serve_points = (
            server.first_serve_pct * 
            server.first_serve_win_pct * 
            (2 - returner.return_win_pct)
        )
        
        second_serve_points = (
            (1 - server.first_serve_pct) * 
            server.second_serve_win_pct * 
            (2 - returner.return_win_pct)
        )
        
        point_win_prob = (first_serve_points + second_serve_points) / 2
        
        # Apply surface adjustment
        point_win_prob *= self.surface_adjustments.get(surface, 1.0)
        
        return self.probability_hold_serve(point_win_prob)
    
    def probability_hold_serve(self, p: float) -> float:
        """Calculate probability of holding serve given probability of winning a point."""
        p = min(max(p, 0.0), 1.0)  # Clamp probability between 0 and 1
        
        # Probability of winning at deuce
        p_deuce = p * p / (p * p + (1-p) * (1-p))
        
        # Probability of holding serve from different scores
        p_40_0 = p * p * p
        p_40_15 = p * p * (1-p) * p
        p_40_30 = p * p * (1-p) * (1-p) * p
        p_deuce_games = p * p * (1-p) * (1-p) * p_deuce
        
        return p_40_0 + p_40_15 + p_40_30 + p_deuce_games
    
    def calculate_set_win_probability(self, 
                                   player_a_hold_prob: float, 
                                   player_b_hold_prob: float,
                                   games_a: int,
                                   games_b: int) -> float:
        """Calculate probability of winning a set from current score."""
        if games_a >= 6 and games_a - games_b >= 2:
            return 1.0
        if games_b >= 6 and games_b - games_a >= 2:
            return 0.0
        if games_a == 6 and games_b == 6:
            # Tiebreak probability
            return self.calculate_tiebreak_win_probability(player_a_hold_prob, player_b_hold_prob)
            
        games_needed_a = 6 - games_a
        games_needed_b = 6 - games_b
        
        # Use dynamic programming to calculate win probability
        dp = {}
        
        def recurse(a: int, b: int) -> float:
            if (a, b) in dp:
                return dp[(a, b)]
            
            if a >= games_needed_a and a - b >= 2:
                return 1.0
            if b >= games_needed_b and b - a >= 2:
                return 0.0
            if a == 6 and b == 6:
                return self.calculate_tiebreak_win_probability(player_a_hold_prob, player_b_hold_prob)
                
            # Probability of winning on serve
            if (a + b) % 2 == 0:  # Player A serving
                p = (player_a_hold_prob * recurse(a + 1, b) + 
                     (1 - player_a_hold_prob) * recurse(a, b + 1))
            else:  # Player B serving
                p = (player_b_hold_prob * recurse(a, b + 1) + 
                     (1 - player_b_hold_prob) * recurse(a + 1, b))
                
            dp[(a, b)] = p
            return p
            
        return recurse(0, 0)
    
    def calculate_tiebreak_win_probability(self, 
                                         player_a_point_prob: float, 
                                         player_b_point_prob: float) -> float:
        """Calculate probability of winning a tiebreak."""
        dp = {}
        
        def recurse(a: int, b: int) -> float:
            if (a, b) in dp:
                return dp[(a, b)]
            
            if a >= 7 and a - b >= 2:
                return 1.0
            if b >= 7 and b - a >= 2:
                return 0.0
                
            # Determine server (changes every two points after first point)
            total_points = a + b
            if total_points == 0 or total_points % 4 in (0, 1):
                p = player_a_point_prob
            else:
                p = 1 - player_b_point_prob
                
            result = p * recurse(a + 1, b) + (1 - p) * recurse(a, b + 1)
            dp[(a, b)] = result
            return result
            
        return recurse(0, 0)
    
    def calculate_match_win_probability(self,
                                     player_a_id: str,
                                     player_b_id: str,
                                     best_of_five: bool = False,
                                     current_score: Optional[Tuple[int, int]] = None,
                                     surface: str = 'hard') -> float:
        """Calculate probability of player A winning the match."""
        # Get hold probabilities
        p_hold_a = self.calculate_serve_hold_probability(player_a_id, player_b_id, surface)
        p_hold_b = self.calculate_serve_hold_probability(player_b_id, player_a_id, surface)
        
        # Calculate set win probability
        p_set = self.calculate_set_win_probability(p_hold_a, p_hold_b, 0, 0)
        
        sets_needed = 3 if best_of_five else 2
        if not current_score:
            current_score = (0, 0)
            
        sets_a, sets_b = current_score
        
        # Use dynamic programming to calculate match win probability
        dp = {}
        
        def recurse(a: int, b: int) -> float:
            if (a, b) in dp:
                return dp[(a, b)]
                
            if a >= sets_needed:
                return 1.0
            if b >= sets_needed:
                return 0.0
                
            result = p_set * recurse(a + 1, b) + (1 - p_set) * recurse(a, b + 1)
            dp[(a, b)] = result
            return result
            
        return recurse(sets_a, sets_b)
