# exec_logic.py
from config import EXCHANGE_FEES_CENTS, MIN_EDGE_CENTS, KELLY_FRACTION, MAX_CONTRACTS
import math
import csv
import time

def signal(fair_cents_yes: float, market_cents_yes: float):
    edge = fair_cents_yes - market_cents_yes
    if edge >= (MIN_EDGE_CENTS + EXCHANGE_FEES_CENTS):
        return "BUY_YES", edge
    if -edge >= (MIN_EDGE_CENTS + EXCHANGE_FEES_CENTS):
        return "SELL_YES", -edge
    return "NO_TRADE", 0.0

def size_kelly(fair_cents_yes: float, price_cents_yes: float, bankroll: float):
    p = fair_cents_yes / 100.0
    q = 1 - p
    b = (100 - price_cents_yes) / price_cents_yes if price_cents_yes > 0 else 100.0
    k = (p - q / b)
    stake_frac = max(0.0, min(1.0, k)) * KELLY_FRACTION
    contracts = int(min(MAX_CONTRACTS, bankroll * stake_frac / price_cents_yes))
    return max(0, contracts)

def log_trade(path, row):
    header = ["ts","market","action","fair_cents","price_cents","edge_cents","contracts"]
    exists = False
    try:
        with open(path, "r"):
            exists = True
    except FileNotFoundError:
        exists = False
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(header)
        w.writerow(row)