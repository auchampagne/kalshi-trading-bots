from kalshi_auth import load_private_key_from_file, get_auth_headers
from config import KALSHI_BASE_URL, KALSHI_KEY_ID, KALSHI_KEY_FILE
import requests

def test_kalshi_connection():
    try:
        # Load the private key
        private_key = load_private_key_from_file(KALSHI_KEY_FILE)
        
        # Test endpoint
        method = "GET"
        path = "/trade-api/v2/portfolio/balance"
        
        # Get authentication headers
        headers = get_auth_headers(method, path, private_key, KALSHI_KEY_ID)
        
        # Make the request
        response = requests.get(KALSHI_BASE_URL + path, headers=headers)
        response.raise_for_status()
        
        print("Successfully connected to Kalshi API!")
        print("Balance information:", response.json())
        return True
        
    except Exception as e:
        print(f"Error connecting to Kalshi API: {e}")
        return False

if __name__ == "__main__":
    test_kalshi_connection()
