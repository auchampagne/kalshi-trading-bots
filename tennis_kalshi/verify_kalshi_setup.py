import os
import sys
from pathlib import Path
from kalshi_auth import load_private_key_from_file, get_auth_headers
import requests

def verify_key_file_exists():
    """Check if the private key file exists"""
    key_file = os.getenv("KALSHI_KEY_FILE", "kalshi-key.pem")
    key_path = Path(key_file)
    if not key_path.exists():
        print(f"ERROR: Private key file not found at {key_path.absolute()}")
        print("Please ensure you have saved your private key as 'kalshi-key.pem'")
        return False
    return True

def verify_key_id():
    """Verify that the Key ID is properly set"""
    key_id = os.getenv("KALSHI_KEY_ID", "")
    if not key_id:
        print("ERROR: KALSHI_KEY_ID is not set in your environment")
        return False
    if key_id != "169ee023-6423-44fe-813e-0498d2369cfa":
        print(f"WARNING: Current Key ID ({key_id}) doesn't match expected ID")
        return False
    return True

def test_api_connection():
    """Test the connection to Kalshi API"""
    try:
        base_url = os.getenv("KALSHI_BASE_URL", "https://demo-api.kalshi.co/trade-api/v2")
        key_id = os.getenv("KALSHI_KEY_ID")
        key_file = os.getenv("KALSHI_KEY_FILE", "kalshi-key.pem")

        # Load private key
        try:
            private_key = load_private_key_from_file(key_file)
        except Exception as e:
            print(f"ERROR: Failed to load private key: {e}")
            return False

        # Test endpoints - start with a simple endpoint
        endpoints = [
            ("GET", "/user", "User Info")
        ]

        for method, path, name in endpoints:
            print(f"\nTesting {name} endpoint...")
            headers = get_auth_headers(method, path, private_key, key_id)
            
            try:
                response = requests.request(method, f"{base_url}{path}", headers=headers)
                response.raise_for_status()
                print(f"✓ {name} API call successful")
                print(f"Response: {response.json()}")
            except requests.exceptions.RequestException as e:
                print(f"✗ {name} API call failed: {e}")
                if response.status_code == 401:
                    print("Authentication failed. Please verify your Key ID and private key.")
                return False

        return True

    except Exception as e:
        print(f"ERROR: Unexpected error during API test: {e}")
        return False

def main():
    print("=== Kalshi API Configuration Verification ===\n")
    
    # Check environment
    print("1. Checking environment variables...")
    if not verify_key_id():
        sys.exit(1)
    print("✓ Key ID verified\n")

    print("2. Checking private key file...")
    if not verify_key_file_exists():
        sys.exit(1)
    print("✓ Private key file found\n")

    print("3. Testing API connection...")
    if not test_api_connection():
        sys.exit(1)
    print("\n✓ All API tests passed successfully!")

if __name__ == "__main__":
    main()
