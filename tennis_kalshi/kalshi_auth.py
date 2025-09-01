from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import base64
import datetime
import os

def load_private_key_from_file(file_path: str) -> rsa.RSAPrivateKey:
    """Load RSA private key from PEM file."""
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,  # or provide password if key is encrypted
            backend=default_backend()
        )
    return private_key

def sign_pss_text(private_key: rsa.RSAPrivateKey, text: str) -> str:
    """Sign text using PSS padding."""
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

def get_auth_headers(method: str, path: str, private_key: rsa.RSAPrivateKey, key_id: str) -> dict:
    """Generate Kalshi API authentication headers."""
    # Get current timestamp in milliseconds
    current_time = datetime.datetime.now()
    timestamp = current_time.timestamp()
    current_time_milliseconds = int(timestamp * 1000)
    timestamp_str = str(current_time_milliseconds)
    
    # Create message string for signing
    msg_string = timestamp_str + method + path
    
    # Generate signature
    signature = sign_pss_text(private_key, msg_string)
    
    # Return headers with proper format
    return {
        'KALSHI-ACCESS-KEY': key_id,
        'KALSHI-ACCESS-SIGNATURE': signature,
        'KALSHI-ACCESS-TIMESTAMP': timestamp_str,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
