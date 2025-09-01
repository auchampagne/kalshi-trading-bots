# Configuration for the Crypto Arbitrage Bot
from typing import Dict, Final
import os
from dotenv import load_dotenv

load_dotenv()

# Crypto API Configuration
CRYPTO_API_KEYS: Final[Dict[str, str]] = {
    'binance': os.getenv('BINANCE_API_KEY', ''),
    'coinbase': os.getenv('COINBASE_API_KEY', ''),
    'kraken': os.getenv('KRAKEN_API_KEY', '')
}

# Kalshi API Configuration
KALSHI_BASE_URL: Final = os.getenv('KALSHI_BASE_URL', 'https://trading-api.kalshi.com/v2')
KALSHI_KEY_ID: Final = os.getenv('KALSHI_KEY_ID', '')
KALSHI_KEY_FILE: Final = os.getenv('KALSHI_KEY_FILE', 'kalshi-key.pem')

# Trading Parameters
MIN_EDGE_PERCENTAGE: Final = float(os.getenv('MIN_EDGE_PERCENTAGE', '0.5'))
MAX_RISK_PERCENTAGE: Final = float(os.getenv('MAX_RISK_PERCENTAGE', '2.0'))
SCAN_INTERVAL_SECONDS: Final = int(os.getenv('SCAN_INTERVAL_SECONDS', '60'))
ORDER_BOOK_DEPTH: Final = int(os.getenv('ORDER_BOOK_DEPTH', '10'))
MOMENTUM_WINDOW: Final = int(os.getenv('MOMENTUM_WINDOW', '20'))
VOLATILITY_WINDOW: Final = int(os.getenv('VOLATILITY_WINDOW', '30'))
MIN_PATTERN_CONFIDENCE: Final = float(os.getenv('MIN_PATTERN_CONFIDENCE', '0.7'))
MAX_ORDER_AGE_MINUTES: Final = int(os.getenv('MAX_ORDER_AGE_MINUTES', '5'))

# Execution Mode
DRY_RUN: Final = os.getenv('DRY_RUN', 'True').lower() == 'true'
