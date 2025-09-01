#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
from tennis_trading_bot import TennisTradingBot

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'SPORTSCORE_API_KEY',
        'KALSHI_KEY_ID',
        'KALSHI_KEY_FILE',
        'KALSHI_DEMO_MODE',
        'MIN_EDGE_CENTS',
        'EXCHANGE_FEES_CENTS',
        'KELLY_FRACTION',
        'MAX_CONTRACTS'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        return False
    return True

def main():
    # Load environment variables
    load_dotenv()
    
    print("🎾 Tennis Trading Bot Startup")
    print("-----------------------------")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Initialize and run bot
    try:
        bot = TennisTradingBot()
        print("✅ Bot initialized successfully")
        print(f"Mode: {'Demo' if bot.demo_mode else 'Production'}")
        print("Starting main loop...")
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Shutting down bot...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
