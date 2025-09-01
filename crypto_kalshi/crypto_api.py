from typing import Dict, List, Optional
import requests
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CryptoPrice:
    symbol: str
    price: float
    timestamp: datetime
    source: str

class CryptoDataClient:
    """Client for fetching cryptocurrency data from multiple sources"""
    
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.base_urls = {
            'binance': 'https://api.binance.com/api/v3',
            'coinbase': 'https://api.coinbase.com/v2',
            'kraken': 'https://api.kraken.com/0/public'
        }

    def get_eth_price(self) -> List[CryptoPrice]:
        """Fetch ETH price from multiple exchanges for arbitrage analysis"""
        prices = []
        
        # Binance
        try:
            binance_response = requests.get(f"{self.base_urls['binance']}/ticker/price", 
                                         params={'symbol': 'ETHUSDT'})
            if binance_response.status_code == 200:
                data = binance_response.json()
                prices.append(CryptoPrice(
                    symbol='ETH',
                    price=float(data['price']),
                    timestamp=datetime.now(),
                    source='binance'
                ))
        except Exception as e:
            print(f"Binance API error: {e}")

        # Add more exchanges here...
        
        return prices

    def get_historical_prices(self, symbol: str, interval: str = '1h') -> List[Dict]:
        """Get historical price data for analysis"""
        # Implementation for historical data
        pass
