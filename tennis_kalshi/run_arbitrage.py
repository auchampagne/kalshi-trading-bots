#!/usr/bin/env python3
import time
import json
from datetime import datetime
from arbitrage_finder import TennisArbitrageFinder

def main():
    finder = TennisArbitrageFinder()
    
    print("🎾 Tennis Arbitrage Bot Started")
    print("--------------------------------")
    
    while True:
        try:
            print(f"\n[{datetime.now()}] Scanning for opportunities...")
            
            # Find opportunities
            opportunities = finder.find_opportunities()
            
            # Log and display opportunities
            for opp in opportunities:
                print("\n🎯 Found Opportunity!")
                print(f"Match: {opp.match_details.home_player} vs {opp.match_details.away_player}")
                print(f"Score: {opp.match_details.home_sets}-{opp.match_details.away_sets} "
                      f"({opp.match_details.current_set_home_games}-{opp.match_details.current_set_away_games})")
                print(f"Market ID: {opp.market_id}")
                print(f"Action: {opp.action}")
                print(f"Fair Price: {opp.fair_price:.2f}c")
                print(f"Market Price: {opp.market_price:.2f}c")
                print(f"Edge: {opp.edge:.2f}c")
                print(f"Recommended Size: {opp.recommended_size} contracts")
                
                # Log to file
                with open('opportunities.json', 'a') as f:
                    json.dump({
                        'timestamp': datetime.now().isoformat(),
                        'market_id': opp.market_id,
                        'fair_price': opp.fair_price,
                        'market_price': opp.market_price,
                        'edge': opp.edge,
                        'size': opp.recommended_size,
                        'action': opp.action,
                        'match': {
                            'home_player': opp.match_details.home_player,
                            'away_player': opp.match_details.away_player,
                            'score': f"{opp.match_details.home_sets}-{opp.match_details.away_sets}"
                        }
                    }, f)
                    f.write('\n')
            
            if not opportunities:
                print("No opportunities found")
            
            # Wait before next scan
            print("\nWaiting 30 seconds before next scan...")
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n\nBot stopped by user")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Retrying in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main()
