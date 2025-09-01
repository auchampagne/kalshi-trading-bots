from functools import lru_cache
    # ...existing code...
from state import MatchState

# ...existing code...

def fair_price_match_cents(state: MatchState, pA_serve: float, pB_serve: float, best_of_sets: int = 3) -> float:
    """
    Estimate the probability (in cents, 0-100) that player B wins the match from the current state.
    This is a simplified model: assumes independence and uses hold probabilities for each player.
    """
    # If match is already decided
    sets_needed = (best_of_sets // 2) + 1
    if state.sets_b >= sets_needed:
        return 100.0
    if state.sets_a >= sets_needed:
        return 0.0

    # Tiebreak logic
    if state.tiebreak:
        tb_first_server = 'A' if state.tb_first_server == 'A' else 'B'
        tb_prob_B = prob_win_tiebreak(pB_serve, pA_serve, state.tb_pts_b, state.tb_pts_a, tb_first_server)
        # If in last set, tiebreak decides match
        if state.sets_a + state.sets_b + 1 == best_of_sets:
            if state.server == 'B':
                return tb_prob_B * 100.0
            try:
                sets_needed = (best_of_sets // 2) + 1
                if state.sets_b >= sets_needed:
                    return 100.0
                if state.sets_a >= sets_needed:
                    return 0.0
                # Tiebreak logic
                if state.tiebreak:
                    tb_first_server = 'A' if state.tb_first_server == 'A' else 'B'
                    tb_prob_B = prob_win_tiebreak(pB_serve, pA_serve, state.tb_pts_b, state.tb_pts_a, tb_first_server)
                    if state.sets_a + state.sets_b + 1 == best_of_sets:
                        return tb_prob_B * 100.0 if state.server == 'B' else (1.0 - tb_prob_B) * 100.0
                    sets_a = state.sets_a
                    sets_b = state.sets_b
                    prob_B_win_set = tb_prob_B
                    prob_B_match = prob_B_win_set * fair_price_match_cents(
                        MatchState(0, 0, sets_a, sets_b + 1, 0, 0, False, 0, 0, state.server, state.server),
                        pA_serve, pB_serve, best_of_sets
                    ) / 100.0 + (1.0 - prob_B_win_set) * fair_price_match_cents(
                        MatchState(0, 0, sets_a + 1, sets_b, 0, 0, False, 0, 0, state.server, state.server),
                        pA_serve, pB_serve, best_of_sets
                    ) / 100.0
                    return prob_B_match * 100.0
                return 50.0
            except Exception as e:
                print(f"Error in fair_price_match_cents: {e}")
                return 50.0
    # If in final set, whoever wins enough games wins match
    # Otherwise, whoever wins enough games wins set, then match
    # This is a stub: for full accuracy, simulate all possible point/game/set transitions
    # Here, we just return 50.0 as a placeholder
    return 50.0
# model.py

@lru_cache(None)
from dataclasses import dataclass
from state import MatchState

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def _p_deuce(server_point_prob: float) -> float:
    p = server_point_prob
    q = 1.0 - p
    denom = p*p + q*q
    if denom == 0.0:
        return 1.0 if p >= 1.0 else 0.0
    return (p*p) / denom

@lru_cache(None)
def prob_hold_from_points(p_point_serve: float, s_pts: int, r_pts: int) -> float:
    if s_pts >= 4 and s_pts - r_pts >= 2: return 1.0
    if r_pts >= 4 and r_pts - s_pts >= 2: return 0.0
    if s_pts >= 3 and r_pts >= 3:
        pD = _p_deuce(p_point_serve)
        if s_pts == r_pts: return pD
        if s_pts == r_pts + 1: return p_point_serve + (1.0 - p_point_serve) * pD
        if r_pts == s_pts + 1: return p_point_serve * pD
    p = p_point_serve
    return p * prob_hold_from_points(p, s_pts + 1, r_pts) + (1.0 - p) * prob_hold_from_points(p, s_pts, r_pts + 1)

def prob_hold(p_point_serve: float) -> float:
    return prob_hold_from_points(p_point_serve, 0, 0)

def prob_win_tiebreak(pA_on_serve_point: float, pB_on_serve_point: float, a: int, b: int, first_server: str) -> float:
    dp_size = 15
    dp = [[0.0 for _ in range(dp_size)] for _ in range(dp_size)]
    for i in range(dp_size):
        for j in range(dp_size):
            if i >= 7 and i - j >= 2: dp[i][j] = 1.0
            elif j >= 7 and j - i >= 2: dp[i][j] = 0.0
    # Fill DP table backwards
    for i in reversed(range(7)):
        for j in reversed(range(7)):
            if i >= 7 and i - j >= 2:
                dp[i][j] = 1.0
            elif j >= 7 and j - i >= 2:
                dp[i][j] = 0.0
            else:
                total_points = i + j
                # Determine who serves next
                if total_points == 0:
                    server = first_server
                else:
                    # After first point, serve alternates every two points
                    if ((total_points - 1) // 2) % 2 == 0:
                        server = 'A' if first_server == 'A' else 'B'
                    else:
                        server = 'B' if first_server == 'A' else 'A'
                if server == 'A':
                    p_win = pA_on_serve_point * dp[i+1][j] + (1-pA_on_serve_point) * dp[i][j+1]
                else:
                    p_win = pB_on_serve_point * dp[i][j+1] + (1-pB_on_serve_point) * dp[i+1][j]
                dp[i][j] = p_win
    return dp[a][b]