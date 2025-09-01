# run_paper.py
import time
import requests
import json
from state import MatchState
from updater import ServeModel, ServePriors
from model import fair_price_match_cents
from exec_logic import signal, size_kelly, log_trade
from config import (
    ADAPTIVE_DISCOUNT_BASE,
    BEST_OF_SETS
)

# --- SportScore API Configuration ---
SPORTSCORE_API_KEY = "aeed93b7a2mshd66c54ef283fb13p14f4f3jsn9c2d7d8fdc68"
SPORTSCORE_BASE_URL = "https://sportscore1.p.rapidapi.com"
SPORTSCORE_HEADERS = {
    "x-rapidapi-key": SPORTSCORE_API_KEY,
    "x-rapidapi-host": "sportscore1.p.rapidapi.com"
}
TENNIS_SPORT_ID = 2 # The ID for Tennis is 2

def parse_point_string(p_str: str) -> int:
    """
    Translates a point string ('0', '15', '30', '40', 'AD') into a number.
    You will need to confirm what the API sends for 'Advantage'.
    """
    if p_str == '15': return 1
    if p_str == '30': return 2
    if p_str == '40': return 3
    if p_str.upper() == 'AD': return 4 # Assumption
    return 0

def parse_event_to_state(event_data: dict) -> MatchState | None:
    """
    Parses the JSON data from the SportScore API into our MatchState object.
    This version is based on the real Tennis JSON you received.
    """
    try:
        home_score = event_data['home_score']
        away_score = event_data['away_score']

        server_indicator = event_data.get('first_supply')
        server = 'A' if server_indicator == 1 else 'B'
        
        last_period_str = event_data.get("lasted_period", "period_1")
        
        current_games_a = int(home_score.get(last_period_str, 0))
        current_games_b = int(away_score.get(last_period_str, 0))

        is_tiebreak = (current_games_a == 6 and current_games_b == 6)
        
        state = MatchState(
            sets_a=int(home_score.get('current', 0)),
            sets_b=int(away_score.get('current', 0)),
            set_games_a=current_games_a,
            set_games_b=current_games_b,
            pts_a=parse_point_string(home_score.get('point', '0')),
            pts_b=parse_point_string(away_score.get('point', '0')),
            server=server,
            tiebreak=is_tiebreak,
            tb_pts_a=parse_point_string(home_score.get('point', '0')) if is_tiebreak else 0,
            tb_pts_b=parse_point_string(away_score.get('point', '0')) if is_tiebreak else 0
        )
        return state
    except (KeyError, TypeError, ValueError) as e:
        print(f"--> Could not parse event. Data might be incomplete. Error: {e}")
        return None

def main_loop():
    """ The main operational loop for the trading bot. """
    priors = ServePriors()
    serve_model = ServeModel(priors)
    bankroll_cents = 100000.0

    print("🚀 Trading bot started. Polling for live tennis matches...")
    while True:
        try:
            url = f"{SPORTSCORE_BASE_URL}/sports/{TENNIS_SPORT_ID}/events/live"
            response = requests.get(url, headers=SPORTSCORE_HEADERS)
            response.raise_for_status()
            live_events = response.json().get('data', [])

            if not live_events:
                print("No live matches found. Waiting...")
                time.sleep(60)
                continue
            
            print(f"\nFound {len(live_events)} live match(es).")

            for event in live_events:
                match_name = f"{event.get('home_team',{}).get('name')} vs {event.get('away_team',{}).get('name')}"
                
                state = parse_event_to_state(event)
                if not state:
                    print(f"Skipping match: {match_name} (Could not parse state)")
                    continue

                print(f"--- Processing: {match_name} | Score: {state.sets_a}-{state.sets_b}, {state.set_games_a}-{state.set_games_b} ---")

                best_of_sets = event.get('default_period_count', 3)
                
                fair_A = fair_price_match_cents(state, serve_model.current_pA(), serve_model.current_pB(), best_of_sets)
                fair_B = 100.0 - fair_A
                
                market_odds = event.get('main_odds', {}).get('outcome_2', {}).get('value')
                if market_odds:
                    market_prob = 1 / market_odds
                    market_B = market_prob * 100
                else:
                    market_B = 50.0 # Default if no odds are available

                action, edge = signal(fair_B, market_B)
                contracts = size_kelly(fair_B, market_B, bankroll_cents)
                print(f"Fair Value (B): {fair_B:.2f}c | Market: {market_B:.2f}c -> {action} w/ {contracts} contracts")
            
            print("\nFinished polling run. Waiting 30 seconds...")
            time.sleep(30)

        except requests.exceptions.RequestException as e:
            print(f"An API error occurred: {e}. Retrying...")
            time.sleep(60)
        except KeyboardInterrupt:
            print("\nBot stopped manually.")
            break

if __name__ == "__main__":
    main_loop()