"""
kalshi.py — Kalshi + Polymarket prediction market data.
Dynamically discovers high-volume, crisis-relevant markets.
All prices from last_price_dollars (0.0–1.0 scale → multiply by 100 for %).
"""

import json
import requests
import streamlit as st

KALSHI_API = "https://api.elections.kalshi.com/trade-api/v2"

CRISIS_KEYWORDS = [
    "oil", "wti", "crude", "opec",
    "recession", "gdp", "unemployment", "inflation", "cpi", "fed", "rate",
    "iran", "hormuz", "sanctions", "tariff", "trade war", "trade deal",
    "war", "conflict", "nato", "china", "taiwan", "russia", "ukraine",
    "default", "debt ceiling", "treasury", "market", "crash", "s&p", "dow",
    "military", "nuclear", "missile",
]

MAX_KALSHI = 4
MAX_POLYMARKET = 3


def _is_crisis_relevant(text: str) -> bool:
    low = text.lower()
    return any(kw in low for kw in CRISIS_KEYWORDS)


def _extract_price(market: dict) -> float:
    price = market.get("last_price_dollars") or market.get("previous_yes_bid_dollars") or 0
    return float(price)


@st.cache_data(ttl=600)
def fetch_kalshi_markets() -> list:
    """Fetch high-volume crisis-relevant markets from Kalshi."""
    try:
        r = requests.get(
            f"{KALSHI_API}/markets",
            params={"status": "open", "limit": 200},
            timeout=10,
        )
        r.raise_for_status()
        markets = r.json().get("markets", [])
        if not markets:
            return [{"source": "kalshi", "error": "no open markets returned"}]

        scored = []
        for m in markets:
            title = m.get("title", "")
            volume = int(m.get("volume", 0) or 0)
            relevant = _is_crisis_relevant(title)
            scored.append((m, volume, relevant))

        # crisis-relevant markets sorted by volume
        relevant = [(m, v) for m, v, rel in scored if rel and v > 0]
        relevant.sort(key=lambda x: x[1], reverse=True)

        # if fewer than 2 relevant, pad with top-volume markets
        if len(relevant) < 2:
            all_by_vol = [(m, v) for m, v, _ in scored if v > 0]
            all_by_vol.sort(key=lambda x: x[1], reverse=True)
            existing_tickers = {m.get("ticker") for m, _ in relevant}
            for m, v in all_by_vol:
                if m.get("ticker") not in existing_tickers:
                    relevant.append((m, v))
                    existing_tickers.add(m.get("ticker"))
                if len(relevant) >= MAX_KALSHI:
                    break

        results = []
        for m, vol in relevant[:MAX_KALSHI]:
            price = _extract_price(m)
            results.append({
                "source":  "kalshi",
                "ticker":  m.get("ticker", ""),
                "title":   m.get("title", ""),
                "yes_pct": round(price * 100, 1),
                "volume":  vol,
                "error":   None,
            })
        return results if results else [{"source": "kalshi", "error": "no markets with volume"}]
    except Exception as e:
        return [{"source": "kalshi", "error": str(e)[:80]}]


@st.cache_data(ttl=600)
def fetch_polymarket_odds() -> list:
    """Fetch high-volume crisis-relevant markets from Polymarket."""
    try:
        r = requests.get(
            "https://gamma-api.polymarket.com/markets",
            params={"active": "true", "limit": 100, "order": "volume", "ascending": "false"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            return [{"source": "polymarket", "error": "no active markets returned"}]

        relevant = []
        fallback = []
        for item in data:
            question = item.get("question", "")
            volume = float(item.get("volume", 0) or 0)
            if _is_crisis_relevant(question) and volume > 0:
                relevant.append((item, volume))
            elif volume > 0 and len(fallback) < MAX_POLYMARKET:
                fallback.append((item, volume))

        # pad with fallback if too few relevant
        if len(relevant) < 2:
            existing_qs = {item.get("question") for item, _ in relevant}
            for item, vol in fallback:
                if item.get("question") not in existing_qs:
                    relevant.append((item, vol))
                if len(relevant) >= MAX_POLYMARKET:
                    break

        relevant.sort(key=lambda x: x[1], reverse=True)

        results = []
        for item, vol in relevant[:MAX_POLYMARKET]:
            prices = json.loads(item.get("outcomePrices", '["0","1"]'))
            results.append({
                "source":   "polymarket",
                "title":    item.get("question", ""),
                "yes_pct":  round(float(prices[0]) * 100, 1),
                "volume":   vol,
                "error":    None,
            })
        return results if results else [{"source": "polymarket", "error": "no markets with volume"}]
    except Exception as e:
        return [{"source": "polymarket", "error": str(e)[:80]}]


def format_markets_for_prompt(kalshi: list, polymarket: list) -> str:
    lines = ["PREDICTION MARKETS (live odds):"]

    kalshi_valid = [m for m in kalshi if not m.get("error")]
    if kalshi_valid:
        for m in kalshi_valid:
            lines.append(f"- Kalshi: {m['title']} — {m['yes_pct']}% YES [{m.get('ticker','')}]")
    else:
        lines.append("- Kalshi markets: unavailable")

    poly_valid = [m for m in polymarket if not m.get("error")]
    if poly_valid:
        for m in poly_valid:
            lines.append(f"- Polymarket: {m['title']} — {m['yes_pct']}% YES")
    else:
        lines.append("- Polymarket markets: unavailable")

    return "\n".join(lines)
