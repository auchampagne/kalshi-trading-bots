# tennis_kalshi/updater.py
from dataclasses import dataclass
from config import ADAPTIVE_DISCOUNT_BASE

@dataclass
class ServePriors:
    a_alpha: float = 30.0
    a_beta: float = 20.0
    b_alpha: float = 40.0
    b_beta: float = 18.0

class ServeModel:
    def __init__(self, priors: ServePriors):
        self.a_alpha = priors.a_alpha
        self.a_beta = priors.a_beta
        self.b_alpha = priors.b_alpha
        self.b_beta = priors.b_beta
        # --- NEW: Track service games played for adaptive discount ---
        self.a_service_games_played = 0
        self.b_service_games_played = 0

    def current_pA(self) -> float:
        return self.a_alpha / (self.a_alpha + self.a_beta)

    def current_pB(self) -> float:
        return self.b_alpha / (self.b_alpha + self.b_beta)
        
    def _get_adaptive_discount(self, player: str) -> float:
        """
        Calculates a discount factor that increases as more data is collected.
        The formula 1 / (N + C) is a simple way to decrease the influence of the
        base constant 'C' as the number of games 'N' grows.
        """
        if player == 'A':
            games_played = self.a_service_games_played
        else:
            games_played = self.b_service_games_played
        
        # This ensures the discount factor starts smaller and grows towards 1.0
        # as more games are played, making the model more responsive over time.
        return 1.0 / (games_played + ADAPTIVE_DISCOUNT_BASE)

    def update_after_service_game(self, server: str, points_won_by_server: int, total_points: int):
        points_lost = total_points - points_won_by_server
        if total_points <= 0:
            return
            
        # --- UPDATED: Use the adaptive discount factor ---
        d = self._get_adaptive_discount(server)
        
        if server == 'A':
            # The update formula now uses the dynamic 'd'
            self.a_alpha += d * (points_won_by_server - self.current_pA() * total_points)
            self.a_beta += d * (points_lost - (1 - self.current_pA()) * total_points)
            self.a_service_games_played += 1 # Increment the counter
        else:
            self.b_alpha += d * (points_won_by_server - self.current_pB() * total_points)
            self.b_beta += d * (points_lost - (1 - self.current_pB()) * total_points)
            self.b_service_games_played += 1 # Increment the counter