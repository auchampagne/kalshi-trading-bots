#!/usr/bin/env python3
import os
import logging
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from enum import Enum

class Environment(Enum):
    DEMO = "demo"
    PROD = "prod"

class KalshiClient:
    """Real Kalshi client implementation."""
    
    def __init__(self, key_id: str, private_key: Any, environment: Environment = Environment.DEMO):
        self.key_id = key_id
        self.private_key = private_key
        self.environment = environment
        self.base_url = (
            "https://demo-api.kalshi.co/trade-api/v2" 
            if environment == Environment.DEMO 
            else "https://trading-api.kalshi.com/v2"
        )
        
    def _sign_request(self, method: str, path: str) -> str:
        """Sign request using PSS padding."""
        timestamp = str(int(datetime.now().timestamp() * 1000))
        message = f"{timestamp}{method}{path}".encode('utf-8')
        
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature.hex()
        
    def _get_headers(self, method: str, path: str) -> Dict[str, str]:
        """Get request headers with authentication."""
        timestamp = str(int(datetime.now().timestamp() * 1000))
        return {
            'Authorization': f"Kalshi {self.key_id}:{self._sign_request(method, path)}",
            'Kalshi-Ts': timestamp,
            'Content-Type': 'application/json'
        }
        
    def _request(self, method: str, path: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to Kalshi API."""
        url = f"{self.base_url}{path}"
        headers = self._get_headers(method, path)
        
        response = requests.request(method, url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
        
    def get_markets(self, series_ticker: Optional[str] = None, status: Optional[str] = None) -> list:
        """Get markets matching criteria."""
        params = []
        if series_ticker:
            params.append(f"series={series_ticker}")  # Correct parameter name
        if status:
            params.append(f"status={status}")
            
        path = f"/markets{'?' + '&'.join(params) if params else ''}"
        response = self._request('GET', path)
        return response.get('markets', [])
        
    def get_market(self, market_id: str) -> Dict:
        """Get specific market details."""
        return self._request('GET', f"/markets/{market_id}")
        
    def create_order(self, 
                    market_id: str,
                    side: str,
                    price_cents: int,
                    size: int,
                    order_type: str = 'limit') -> Dict:
        """Create a new order."""
        data = {
            'action': side.lower(),
            'count': size,
            'market_id': market_id,
            'price': price_cents,
            'type': order_type
        }
        return self._request('POST', '/orders', data)
        
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an existing order."""
        return self._request('DELETE', f'/orders/{order_id}')
        
    def get_balance(self) -> Dict:
        """Get current balance."""
        return self._request('GET', '/portfolio/balance')
        
    def get_positions(self) -> Dict:
        """Get current positions."""
        return self._request('GET', '/portfolio/positions')
