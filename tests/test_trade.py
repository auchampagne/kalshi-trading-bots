import os
from dotenv import load_dotenv
from tennis_trading_bot import TennisTradingBot
import logging

def test_single_trade():
    # Load environment variables
    load_dotenv()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    try:
        # Initialize the bot
        print("🎾 Initializing Tennis Trading Bot...")
        bot = TennisTradingBot()
        
        # Find opportunities
        print("\n🔍 Searching for trading opportunities...")
        opportunities = bot.find_opportunities()
        
        if not opportunities:
            print("No trading opportunities found at this time.")
            return
        
        # Display opportunities
        print(f"\n📊 Found {len(opportunities)} potential opportunities:")
        for i, opp in enumerate(opportunities, 1):
            analysis = opp['analysis']
            print(f"\nOpportunity #{i}:")
            print(f"Market: {analysis['title']}")
            print(f"Edge: {opp['edge']:.2f} cents")
            print(f"Recommended Side: {analysis['recommended_side']}")
            print(f"Kelly Fraction: {float(analysis['kelly_fraction']):.3f}")
            print(f"Model Probability: {analysis['model_probability']:.2%}")
            print(f"Current Yes Price: {analysis['yes_price']}")
            print(f"Current No Price: {analysis['no_price']}")
        
        # Execute first opportunity
        print("\n💫 Executing trade for first opportunity...")
        first_opp = opportunities[0]
        trade_result = bot.tennis_trader.place_tennis_trade(
            market_id=first_opp['market_id'],
            side=first_opp['analysis']['recommended_side'],
            size=first_opp['analysis']['kelly_fraction']
        )
        
        # Display trade result
        if trade_result.get('error'):
            print(f"❌ Trade Error: {trade_result['error']}")
        else:
            print("✅ Trade executed successfully!")
            print(f"Order ID: {trade_result.get('order_id')}")
            print(f"Size: {trade_result.get('size')} contracts")
            print(f"Price: {trade_result.get('price')} cents")
            
        # Monitor position
        print("\n📈 Monitoring position for 1 minute...")
        bot.manage_positions()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_single_trade()
