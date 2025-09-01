import requests
import json

# --- Configuration ---
API_KEY = "aeed93b7a2mshd66c54ef283fb13p14f4f3jsn9c2d7d8fdc68"
BASE_URL = "https://sportscore1.p.rapidapi.com"
HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "sportscore1.p.rapidapi.com"
}

def get_sport_id(sport_name: str) -> int | None:
    """Finds the numerical ID for a given sport from the API."""
    url = f"{BASE_URL}/sports"
    print(f"Finding sport ID for {sport_name}...")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        sports = response.json().get('data', [])
        for sport in sports:
            if sport.get('name') == sport_name:
                print(f"Found {sport_name} with sport_id: {sport['id']}")
                return sport['id']
        print(f"Error: Could not find '{sport_name}' in the sport list.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An API error occurred: {e}")
        return None

def get_live_events(sport_id: int):
    """Fetches all live events for a given sport ID."""
    url = f"{BASE_URL}/sports/{sport_id}/events/live"
    print("\nFetching live events...")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        live_events = response.json().get('data', [])
        if not live_events:
            print("No live tennis matches found at the moment.")
            return
        print(f"Found {len(live_events)} live match(es).")
        print("--- Example Tennis Match Data ---")
        print(json.dumps(live_events[0], indent=2))
    except requests.exceptions.RequestException as e:
        print(f"An API error occurred: {e}")

if __name__ == "__main__":
    tennis_id = get_sport_id("Tennis")
    if tennis_id:
        get_live_events(tennis_id)

