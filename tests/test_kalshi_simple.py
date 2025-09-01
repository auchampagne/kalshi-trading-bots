from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import base64
import requests
import datetime
import os

def load_private_key_from_file(file_path):
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,  # or provide a password if your key is encrypted
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

def main():
    # Load your private key
    private_key = load_private_key_from_file('kalshi-key.pem')
    
    # Get current timestamp in milliseconds
    current_time = datetime.datetime.now()
    timestamp = current_time.timestamp()
    current_time_milliseconds = int(timestamp * 1000)
    timestamp_str = str(current_time_milliseconds)
    
    # API configuration
    method = "GET"
    base_url = 'https://demo-api.kalshi.co'
    path = '/trade-api/v2/portfolio/balance'
    
    # Create signature
    msg_string = timestamp_str + method + path
    sig = sign_pss_text(private_key, msg_string)
    
    # Set up headers exactly as in the example
    headers = {
        'KALSHI-ACCESS-KEY': '169ee023-6423-44fe-813e-0498d2369cfa',
        'KALSHI-ACCESS-SIGNATURE': sig,
        'KALSHI-ACCESS-TIMESTAMP': timestamp_str
    }
    
    print(f"Making request to: {base_url + path}")
    print("Headers:", headers)
    
    # Make the request
    try:
        response = requests.get(base_url + path, headers=headers)
        response.raise_for_status()
        print("\nResponse:", response.text)
    except requests.exceptions.RequestException as e:
        print(f"\nError: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response body: {e.response.text}")

if __name__ == "__main__":
    main()
