from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import base64
import requests
import datetime
import time

class Environment(Enum):
    DEMO = "demo"
    PROD = "prod"

@dataclass
class MarketQuote:
    market_id: str
    best_bid_price: Optional[int]  # in cents
    best_ask_price: Optional[int]  # in cents
    last_price: Optional[int]
    bid_depth: int
    ask_depth: int

class KalshiClient:
    def __init__(self, key_id: str, private_key: rsa.RSAPrivateKey, environment: Environment = Environment.DEMO):
        self.key_id = key_id
        self.private_key = private_key
        
        if environment == Environment.DEMO:
            self.base_url = "https://demo-api.kalshi.co"
        else:
            self.base_url = "https://api.elections.kalshi.com"
    
    def request_headers(self, method: str, path: str) -> dict:
        timestamp = str(int(datetime.datetime.now().timestamp() * 1000))
        msg_string = timestamp + method + path
        signature = self._sign_pss_text(msg_string)
        
        return {
            'KALSHI-ACCESS-KEY': self.key_id,
            'KALSHI-ACCESS-SIGNATURE': signature,
            'KALSHI-ACCESS-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }

    def _sign_pss_text(self, text: str) -> str:
        message = text.encode('utf-8')
        try:
            signature = self.private_key.sign(
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH
                ),
                hashes.SHA256()
            )
            return base64.b64encode(signature).decode('utf-8')
        except InvalidSignature as e:
            raise ValueError("RSA sign PSS failed") from e

    def get_market_quote(self, market_id: str) -> MarketQuote:
        """Get current market quotes for a specific market."""
        method = "GET"
        path = f"/trade-api/v2/markets/{market_id}/orderbook"
        headers = self.request_headers(method, path)
        
        response = requests.get(f"{self.base_url}{path}", headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Process orderbook data
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        
        return MarketQuote(
            market_id=market_id,
            best_bid_price=max([b['price'] for b in bids]) if bids else None,
            best_ask_price=min([a['price'] for a in asks]) if asks else None,
            last_price=data.get('last_price'),
            bid_depth=sum(b['size'] for b in bids),
            ask_depth=sum(a['size'] for a in asks)
        )

    def place_order(self, market_id: str, side: str, price_cents: int, size: int) -> Dict[str, Any]:
        """Place a limit order in a market."""
        method = "POST"
        path = "/trade-api/v2/orders"
        headers = self.request_headers(method, path)
        
        payload = {
            "market_id": market_id,
            "side": side,  # "yes" or "no"
            "type": "limit",
            "size": size,
            "price": price_cents,
            "time_in_force": "ioc"  # immediate-or-cancel
        }
        
        response = requests.post(f"{self.base_url}{path}", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        method = "GET"
        path = "/trade-api/v2/portfolio/positions"
        headers = self.request_headers(method, path)
        
        response = requests.get(f"{self.base_url}{path}", headers=headers)
        response.raise_for_status()
        return response.json().get('positions', [])

    def get_balance(self) -> int:
        """Get current balance in cents."""
        method = "GET"
        path = "/trade-api/v2/portfolio/balance"
        headers = self.request_headers(method, path)
        
        response = requests.get(f"{self.base_url}{path}", headers=headers)
        response.raise_for_status()
        return response.json().get('balance', 0)

    def find_tennis_markets(self) -> List[Dict[str, Any]]:
        """Find all available tennis markets."""
        method = "GET"
        path = "/trade-api/v2/markets"
        headers = self.request_headers(method, path)
        
        params = {
            "status": "open",
            "category": "TENNIS"  # Adjust based on actual category name
        }
        
        response = requests.get(f"{self.base_url}{path}", headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('markets', [])
