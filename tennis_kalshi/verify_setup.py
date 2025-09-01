import os
from dotenv import load_dotenv
import sys

def verify_setup():
    # Load environment variables
    load_dotenv()
    
    required_vars = {
        'SPORTSCORE_API_KEY': 'SportScore API key for tennis data',
        'KALSHI_KEY_ID': 'Kalshi API key ID',
        'KALSHI_KEY_FILE': 'Path to Kalshi private key file',
        'KALSHI_DEMO_MODE': 'Whether to use demo mode (True/False)',
        'MIN_EDGE_CENTS': 'Minimum edge required for trades',
        'EXCHANGE_FEES_CENTS': 'Exchange fees in cents',
        'KELLY_FRACTION': 'Kelly criterion fraction',
        'MAX_CONTRACTS': 'Maximum contracts per trade'
    }
    
    missing = []
    print("\n🔍 Checking environment setup...")
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"❌ {var}: Missing - {description}")
        else:
            masked_value = '***' if 'KEY' in var else value
            print(f"✅ {var}: {masked_value}")
    
    if missing:
        print("\n❌ Missing required environment variables:")
        for msg in missing:
            print(msg)
        return False
        
    # Verify Kalshi key file exists
    key_file = os.getenv('KALSHI_KEY_FILE')
    if not os.path.exists(key_file):
        print(f"\n❌ Kalshi private key file not found: {key_file}")
        return False
    
    print("\n✅ All required environment variables are set!")
    return True

if __name__ == "__main__":
    if not verify_setup():
        sys.exit(1)
