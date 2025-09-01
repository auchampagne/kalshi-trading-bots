# tennis_kalshi/config.py
import os
from typing import Final

# ---- SportScore API Configuration ----
SPORTSCORE_BASE_URL: Final = os.getenv("SPORTSCORE_BASE_URL", "https://sportscore1.p.rapidapi.com")
SPORTSCORE_API_KEY: Final = os.getenv("SPORTSCORE_API_KEY", "")
TENNIS_SPORT_ID: Final = 2  # The ID for Tennis in SportScore API

# ---- Kalshi API Configuration ----
KALSHI_BASE_URL = os.getenv("KALSHI_BASE_URL", "https://trading-api.kalshi.com/v2")
KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID", "")  # Your Kalshi API Key ID
KALSHI_KEY_FILE = os.getenv("KALSHI_KEY_FILE", "kalshi-key.pem")  # Path to your private key file
KALSHI_DEMO_MODE = os.getenv("KALSHI_DEMO_MODE", "True") == "True"  # Use demo environment
DRY_RUN = os.getenv("DRY_RUN", "True") == "True"  # Simulate trades without execution
MARKET_TICKER = os.getenv("KALSHI_MARKET_TICKER", "")

# ---- Tennis Model Configuration ----
# The higher this value, the more conservative the model is at the start of a match.
ADAPTIVE_DISCOUNT_BASE = 2.0
# Default match format. The live API data will override this.
BEST_OF_SETS = 3

# ---- Trading and Risk Management Configuration ----
EXCHANGE_FEES_CENTS = float(os.getenv("EXCHANGE_FEES_CENTS", "1.5"))  # cents per contract traded
MIN_EDGE_CENTS = float(os.getenv("MIN_EDGE_CENTS", "2.0"))           # minimum edge required to trade
KELLY_FRACTION = float(os.getenv("KELLY_FRACTION", "0.25"))          # fraction of Kelly bet size
MAX_CONTRACTS = int(os.getenv("MAX_CONTRACTS", "10"))                # maximum position size
MAX_BANKROLL_RISK = float(os.getenv("MAX_BANKROLL_RISK", "0.02"))   # maximum % of bankroll to risk per trade