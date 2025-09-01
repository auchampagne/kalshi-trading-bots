# kalshi_api.py
# Minimal Kalshi REST client (polling). No external deps beyond Python stdlib + 'requests'.
# If endpoints differ on your account, update the URL paths in this file.

import time
import typing as t
import requests
from dataclasses import dataclass
from config import KALSHI_BASE_URL, KALSHI_API_KEY, DRY_RUN

# --------- Helpers ---------

def _headers() -> dict:
    if not KALSHI_API_KEY:
        raise RuntimeError("KALSHI_API_KEY is empty. export KALSHI_API_KEY=... and retry.")
    return {
        "Authorization": f"Bearer {KALSHI_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "tennis-kalshi-bot/0.1",
    }

def _url(path: str) -> str:
    base = KALSHI_BASE_URL.rstrip("/")
    p = path if path.startswith("/") else f"/{path}"
    return f"{base}{p}"

@dataclass
class Orderbook:
    best_bid: t.Optional[int]
    best_ask: t.Optional[int]
    bids: t.List[t.Tuple[int, int]]   # (price_cents, size)
    asks: t.List[t.Tuple[int, int]]

class KalshiClient:
    def __init__(self, timeout: int = 10):
        self.session = requests.Session()
        self.timeout = timeout

    # --- Connectivity checks ---

    def markets_open(self) -> t.List[dict]:
        # Adjust query params if your account uses different filters
        r = self.session.get(_url("/markets"), headers=_headers(), timeout=self.timeout, params={"status":"open"})
        r.raise_for_status()
        data = r.json()
        # Some deployments wrap results in {"markets":[...]} or {"data":{"markets":[...]}}
        if isinstance(data, dict) and "markets" in data:
            return data["markets"]
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict) and "markets" in data["data"]:
            return data["data"]["markets"]
        # Fall back: try to treat it as a list
        if isinstance(data, list):
            return data
        raise RuntimeError(f"Unexpected markets payload: {data}")

    # --- Market data ---

    def get_orderbook(self, market_ticker: str) -> Orderbook:
        if not market_ticker:
            raise ValueError("market_ticker is empty. Set config.MARKET_TICKER or pass explicitly.")
        # Typical path style; update if your API differs
        r = self.session.get(_url(f"/markets/{market_ticker}/orderbook"), headers=_headers(), timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        # Normalize various possible shapes:
        bids = []
        asks = []
        best_bid = None
        best_ask = None

        # Common shapes:
        # {"bids":[{"px": 75, "qty": 10}, ...], "asks":[{"px": 76, "qty": 5}, ...]}
        # or {"orderbook":{"bids":[...],"asks":[...]}}
        ob = data.get("orderbook", data)
        for b in ob.get("bids", []):
            px = b.get("px") or b.get("price") or b.get("p")
            qty = b.get("qty") or b.get("size") or b.get("q")
            if px is not None and qty is not None:
                bids.append((int(px), int(qty)))
        for a in ob.get("asks", []):
            px = a.get("px") or a.get("price") or a.get("p")
            qty = a.get("qty") or a.get("size") or a.get("q")
            if px is not None and qty is not None:
                asks.append((int(px), int(qty)))

        if bids:
            best_bid = max(px for px, _ in bids)
        if asks:
            best_ask = min(px for px, _ in asks)

        return Orderbook(best_bid=best_bid, best_ask=best_ask, bids=bids, asks=asks)

    # --- Trading ---

    def place_yes(self, market_ticker: str, price_cents: int, size: int, tif: str = "IOC") -> dict:
        """
        Places a YES limit order at price_cents for 'size' contracts.
        tif: "IOC" (immediate-or-cancel) or "GTC" depending on your venue.
        """
        payload = {
            "ticker": market_ticker,
            "side": "buy",           # YES side is a buy on the "Yes" contract
            "price": int(price_cents),
            "size": int(size),
            "tif": tif,              # time-in-force
            "type": "limit",
        }
        if DRY_RUN:
            return {"dry_run": True, "submitted": payload}
        r = self.session.post(_url("/orders"), json=payload, headers=_headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def place_no(self, market_ticker: str, price_cents: int, size: int, tif: str = "IOC") -> dict:
        """
        Places a NO (i.e., sell-YES) limit order. Some venues let you specify "side": "sell".
        """
        payload = {
            "ticker": market_ticker,
            "side": "sell",
            "price": int(price_cents),
            "size": int(size),
            "tif": tif,
            "type": "limit",
        }
        if DRY_RUN:
            return {"dry_run": True, "submitted": payload}
        r = self.session.post(_url("/orders"), json=payload, headers=_headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def cancel(self, order_id: str) -> dict:
        if DRY_RUN:
            return {"dry_run": True, "cancelled": order_id}
        r = self.session.delete(_url(f"/orders/{order_id}"), headers=_headers(), timeout=self.timeout)
        r.raise_for_status()
        return r.json()