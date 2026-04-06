"""
kalshi.py — Kalshi + Polymarket prediction market data.
Dynamically discovers high-volume, crisis-relevant markets.

Kalshi:  Uses /events endpoint with category filtering (Economics, Politics,
         Financials, World). Volume field is volume_fp. Prices in last_price_dollars.
Polymarket: Uses /events endpoint sorted by volume, filters out sports/entertainment
         by tag slugs client-side.
"""

import json
import requests
import streamlit as st

KALSHI_API = "https://api.elections.kalshi.com/trade-api/v2"
POLYMARKET_API = "https://gamma-api.polymarket.com"

KALSHI_CATEGORIES = {"Economics", "Politics", "Financials", "World"}

# Polymarket tag slugs to exclude (sports, entertainment, pop culture)
POLY_EXCLUDE_TAGS = {
    "sports", "soccer", "football", "nba", "nfl", "mlb", "nhl", "tennis",
    "cricket", "EPL", "entertainment", "music", "movies", "pop-culture",
    "fifa-world-cup", "2026-fifa-world-cup", "esports", "gaming",
    "mma", "boxing", "formula-1", "f1", "baseball", "hockey", "golf",
    "rugby", "motorsport",
}

# Events with more than this many sub-markets are nominee pools (e.g.
# "Democratic Presidential Nominee 2028" with 128 candidates) — skip them
# since individual sub-markets are meaningless.
MAX_EVENT_MARKETS = 10

MAX_KALSHI = 4
MAX_POLYMARKET = 4


def _extract_price(market: dict) -> float:
    price = market.get("last_price_dollars") or market.get("previous_yes_bid_dollars") or 0
    return float(price)


@st.cache_data(ttl=120)
def fetch_kalshi_markets() -> list:
    """Fetch crisis-relevant markets from Kalshi via events endpoint."""
    try:
        r = requests.get(
            f"{KALSHI_API}/events",
            params={"status": "open", "with_nested_markets": "true", "limit": 100},
            timeout=10,
        )
        r.raise_for_status()
        events = r.json().get("events", [])
        if not events:
            return [{"source": "kalshi", "error": "no open events returned"}]

        results = []
        for evt in events:
            if evt.get("category") not in KALSHI_CATEGORIES:
                continue
            markets = evt.get("markets", [])
            if not markets:
                continue
            # pick the market with the highest volume in this event
            best = max(markets, key=lambda m: float(m.get("volume_fp", 0) or 0))
            vol = float(best.get("volume_fp", 0) or 0)
            price = _extract_price(best)
            results.append({
                "source":  "kalshi",
                "ticker":  best.get("ticker", ""),
                "title":   best.get("title", evt.get("title", "")),
                "yes_pct": round(price * 100, 1),
                "volume":  vol,
                "error":   None,
            })

        # sort by volume descending
        results.sort(key=lambda x: x["volume"], reverse=True)
        return results[:MAX_KALSHI] if results else [{"source": "kalshi", "error": "no relevant markets"}]
    except Exception as e:
        return [{"source": "kalshi", "error": str(e)[:80]}]


@st.cache_data(ttl=120)
def fetch_polymarket_odds() -> list:
    """Fetch high-volume crisis-relevant events from Polymarket."""
    try:
        r = requests.get(
            f"{POLYMARKET_API}/events",
            params={
                "active": "true", "closed": "false",
                "limit": 50, "order": "volume", "ascending": "false",
            },
            timeout=10,
        )
        r.raise_for_status()
        events = r.json()
        if not events:
            return [{"source": "polymarket", "error": "no active events returned"}]

        results = []
        for evt in events:
            # filter out sports/entertainment by tag slugs
            tags = evt.get("tags") or []
            if isinstance(tags, list) and tags and isinstance(tags[0], dict):
                tag_slugs = {t.get("slug", "") for t in tags}
            else:
                tag_slugs = set()
            if tag_slugs & POLY_EXCLUDE_TAGS:
                continue

            vol = float(evt.get("volume", 0) or 0)
            markets = evt.get("markets") or []
            open_markets = [m for m in markets if not m.get("closed") and m.get("outcomePrices")]
            if not open_markets:
                continue
            # skip nominee pools — events with many sub-markets where
            # individual questions are meaningless ("Will Person X win...")
            if len(open_markets) > MAX_EVENT_MARKETS:
                continue
            # pick the market with the highest YES price (most likely outcome)
            def _yes_price(m):
                try:
                    return float(json.loads(m.get("outcomePrices", '["0"]'))[0])
                except (json.JSONDecodeError, IndexError, ValueError):
                    return 0
            best = max(open_markets, key=_yes_price)

            prices = json.loads(best.get("outcomePrices", '["0","1"]'))
            results.append({
                "source":   "polymarket",
                "title":    best.get("question", evt.get("title", "")),
                "yes_pct":  round(float(prices[0]) * 100, 1),
                "volume":   vol,
                "error":    None,
            })

        # already sorted by volume from API, but re-sort after filtering
        results.sort(key=lambda x: x["volume"], reverse=True)
        return results[:MAX_POLYMARKET] if results else [{"source": "polymarket", "error": "no relevant events"}]
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
