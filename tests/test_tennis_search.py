from tennis_data import TennisDataClient
from datetime import datetime, timedelta
import json

def main():
    # Initialize the client with your API key
    client = TennisDataClient("aeed93b7a2mshd66c54ef283fb13p14f4f3jsn9c2d7d8fdc68")
    
    # Get today's date and 7 days ago
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f"Searching for tennis events from {start_date} to {end_date}")
    
    # Search for recent tennis events
    events = client.search_tennis_events(
        date_start=start_date,
        date_end=end_date,
        status='completed'  # Look for completed matches
    )
    
    # Display results
    print(f"\nFound {len(events)} events")
    
    for event in events:
        print("\n-------------------")
        print(f"Match: {event.get('home_team', {}).get('name')} vs {event.get('away_team', {}).get('name')}")
        print(f"Tournament: {event.get('league', {}).get('name')}")
        print(f"Date: {event.get('start_at')}")
        print(f"Score: {event.get('home_score')} - {event.get('away_score')}")
        
        # Save the first event's full data for reference
        if events.index(event) == 0:
            with open('sample_event.json', 'w') as f:
                json.dump(event, f, indent=2)
            print("\nSaved first event data to sample_event.json")

if __name__ == "__main__":
    main()
