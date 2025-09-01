from enum import Enum
from typing import Optional, Dict, Any
import requests
from datetime import datetime
import os

class Environment(Enum):
    DEMO = "demo"
    PROD = "prod"

class KalshiClient:
    def __init__(self, key_id: str, private_key: Any, environment: Environment = Environment.DEMO):
        self.key_id = key_id
        self.private_key = private_key
        self.environment = environment
        self.base_url = "https://demo-api.kalshi.co/trade-api/v2" if environment == Environment.DEMO else "https://trading-api.kalshi.com/v2"
        
    def get_market(self, market_id: str) -> Dict[str, Any]:
        """Demo implementation - returns a mock tennis market."""
        return {
            'id': market_id,
            'title': 'Demo Tennis Market',
            'status': 'active',
            'yes_bid': '65',
            'yes_ask': '68',
            'no_bid': '32',
            'no_ask': '35',
            'volume': '1000',
            'open_interest': '500'
        }
        
    def search_markets(self, series_ticker: str = 'TENNIS', status: str = 'active') -> list:
        """Demo implementation - returns mock tennis markets."""
        return [{
            'id': 'TENNIS-DEMO-1',
            'title': 'Djokovic vs Nadal - Wimbledon Final',
            'status': 'active',
            'series_ticker': 'TENNIS',
            'yes_bid': '65',
            'no_bid': '35'
        }]
        
    def place_order(self, market_id: str, side: str, size: int, price: float) -> Dict[str, Any]:
        """Demo implementation - simulates placing an order."""
        return {
            'order_id': f"demo-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'market_id': market_id,
            'side': side,
            'size': size,
            'price': price,
            'status': 'filled',
            'remaining': 0
        }
        
    def get_portfolio(self) -> Dict[str, Any]:
        """Demo implementation - returns mock portfolio data."""
        return {
            'balance': '10000',
            'buying_power': '10000',
            'total_value': '10000'
        }
