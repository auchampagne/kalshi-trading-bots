from typing import Optional, List, Dict, Any
import requests
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from urllib.parse import urlencode

@dataclass
class TennisMatch:
    home_player: str
    away_player: str
    home_sets: int
    away_sets: int
    current_set_home_games: int
    current_set_away_games: int
    home_points: int
    away_points: int
    server: str  # 'home' or 'away'
    is_tiebreak: bool
    tournament: str
    surface: Optional[str] = None

class TennisDataClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://sportscore1.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "sportscore1.p.rapidapi.com",
            "Content-Type": "application/json"
        }
        self.TENNIS_SPORT_ID = 2
        self.last_request_time = 0
        self.MIN_REQUEST_INTERVAL = 1.0  # Minimum time between requests in seconds

    def get_live_matches(self) -> List[TennisMatch]:
        """Get all live tennis matches with current scores."""
        url = f"{self.base_url}/sports/{self.TENNIS_SPORT_ID}/events/live"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            matches = response.json().get('data', [])
            
            return [self._parse_match_data(match) for match in matches]
        except Exception as e:
            print(f"Error fetching live matches: {e}")
            return []

    def search_tennis_events(self, 
                          date_start: Optional[str] = None,
                          date_end: Optional[str] = None,
                          league_id: Optional[int] = None,
                          status: Optional[str] = None,
                          player_id: Optional[int] = None,
                          page: int = 1) -> List[Dict[str, Any]]:
        """Search for tennis events with various filters."""
        endpoint = f"{self.base_url}/sports/{TENNIS_SPORT_ID}/events"
        
        # Build query parameters
        params = {'page': page}
        if date_start:
            params['date_start'] = date_start
        if date_end:
            params['date_end'] = date_end
        if league_id:
            params['league_id'] = league_id
        if status:
            params['status'] = status
        if player_id:
            params['player_id'] = player_id
            
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        """
        Search for tennis events with various filters.
        
        Args:
            date_start: Start date in format 'YYYY-MM-DD'
            date_end: End date in format 'YYYY-MM-DD'
            league_id: Specific tennis league ID
            status: Event status (e.g., 'live', 'completed', 'postponed')
            player_id: Filter by player ID (will search in both home and away)
            page: Page number for pagination
        
        Returns:
            List of matching tennis events
        """
        # Enforce rate limiting
        current_time = time.time()
        if current_time - self.last_request_time < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - (current_time - self.last_request_time))
        
        # Build query parameters
        params = {
            'page': page,
            'sport_id': self.TENNIS_SPORT_ID
        }
        
        if date_start:
            params['date_start'] = date_start
        if date_end:
            params['date_end'] = date_end
        if league_id:
            params['league_id'] = league_id
        if status:
            params['status'] = status
        if player_id:
            # We'll search for the player in both home and away positions
            params['home_team_id'] = player_id
            params['away_team_id'] = player_id
        
        url = f"{self.base_url}/events/search"
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                params=params,
                json={}  # Empty JSON body as required by the API
            )
            self.last_request_time = time.time()
            
            response.raise_for_status()
            data = response.json()
            
            # Return the events data
            return data.get('data', [])
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching tennis events: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response body: {e.response.text}")
            return []

    def search_player_history(self, 
                            player_id: int, 
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> List[TennisMatch]:
        """
        Search for a player's match history.
        
        Args:
            player_id: The player's ID in the SportScore system
            start_date: Optional start date in format 'YYYY-MM-DD'
            end_date: Optional end date in format 'YYYY-MM-DD'
        
        Returns:
            List of TennisMatch objects representing the player's matches
        """
        if not start_date:
            # Default to last 30 days
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        events = self.search_tennis_events(
            date_start=start_date,
            date_end=end_date,
            player_id=player_id
        )
        
        return [self._parse_match_data(event) for event in events]

    def _parse_match_data(self, match_data: Dict[str, Any]) -> TennisMatch:
        """Parse raw match data into TennisMatch object."""
        home_score = match_data.get('home_score', {})
        away_score = match_data.get('away_score', {})
        
        # Get the current period (set) data
        current_period = match_data.get('lasted_period', 'period_1')
        
        # Parse server information
        server = 'home' if match_data.get('first_supply') == 1 else 'away'
        
        # Current games in the set
        current_set_home = int(home_score.get(current_period, 0))
        current_set_away = int(away_score.get(current_period, 0))
        
        # Check for tiebreak
        is_tiebreak = (current_set_home == 6 and current_set_away == 6)
        
        def parse_point(point_str: str) -> int:
            """Convert tennis point notation to numeric value."""
            points = {'0': 0, '15': 1, '30': 2, '40': 3, 'AD': 4}
            return points.get(point_str, 0)
        
        return TennisMatch(
            home_player=match_data.get('home_team', {}).get('name', ''),
            away_player=match_data.get('away_team', {}).get('name', ''),
            home_sets=int(home_score.get('current', 0)),
            away_sets=int(away_score.get('current', 0)),
            current_set_home_games=current_set_home,
            current_set_away_games=current_set_away,
            home_points=parse_point(home_score.get('point', '0')),
            away_points=parse_point(away_score.get('point', '0')),
            server=server,
            is_tiebreak=is_tiebreak,
            tournament=match_data.get('league', {}).get('name', ''),
            surface=match_data.get('league', {}).get('surface_type')
        )
