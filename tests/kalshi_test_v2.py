from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
from enum import Enum
import base64
import requests
import datetime
import os

class Environment(Enum):
    DEMO = "demo"
    PROD = "prod"

def load_private_key_from_file(file_path):
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

def sign_pss_text(private_key: rsa.RSAPrivateKey, text: str) -> str:
    message = text.encode('utf-8')
    try:
        signature = private_key.sign(
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
        signature = sign_pss_text(self.private_key, msg_string)
        
        return {
            'KALSHI-ACCESS-KEY': self.key_id,
            'KALSHI-ACCESS-SIGNATURE': signature,
            'KALSHI-ACCESS-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }
    
    def get_exchange_status(self):
        """Test endpoint that doesn't require full authentication"""
        method = "GET"
        path = "/trade-api/v2/exchange/status"
        headers = self.request_headers(method, path)
        
        response = requests.get(f"{self.base_url}{path}", headers=headers)
        return response

def main():
    # Load your private key
    private_key = load_private_key_from_file('kalshi-key.pem')
    key_id = "169ee023-6423-44fe-813e-0498d2369cfa"
    
    # Create client
    client = KalshiClient(key_id, private_key, Environment.DEMO)
    
    print("Testing connection to Kalshi API...")
    
    # Try getting exchange status
    try:
        response = client.get_exchange_status()
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Body: {response.text}")
        
        if response.ok:
            print("\nSuccessfully connected to Kalshi API!")
        else:
            print(f"\nError: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
