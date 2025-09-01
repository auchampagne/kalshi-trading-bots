# state.py
from dataclasses import dataclass

@dataclass
class MatchState:
    set_games_a: int
    set_games_b: int
    sets_a: int
    sets_b: int
    pts_a: int
    pts_b: int
    tiebreak: bool = False
    tb_pts_a: int = 0
    tb_pts_b: int = 0
    server: str = 'A'
    tb_first_server: str = 'A'

    @staticmethod
    def starting(server_first: str = 'A'):
        return MatchState(0, 0, 0, 0, 0, 0, False, 0, 0, server_first, server_first)