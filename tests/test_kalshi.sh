#!/bin/bash

# Load environment variables
set -a
source .env
set +a

# Set Kalshi API keys
export KALSHI_KEY_ID="your_key_id"
export KALSHI_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"

# Run the verification script
/Users/apartment/dev/tennis_kalshi/.venv/bin/python tennis_kalshi/verify_kalshi_setup.py
