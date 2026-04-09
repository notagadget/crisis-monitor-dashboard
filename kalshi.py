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

THESIS_KEYWORDS = [
    "hormuz", "iran", "ceasefire", "strait",
    "oil", "nuclear", "persian gulf", "ras laffan",
    "hezbollah", "vance", "pakistan", "sanctions",
    "tehran", "irgc", "khamenei", "war"
]

FALLBACK_KALSHI_CATEGORIES = {"Economics", "Financials"}
MIN_THESIS_MARKETS = 2  # pad with fallback if fewer thesis matches found


def _kalshi_headers() -> dict:
    key = st.secrets.get("KALSHI_API_KEY", "")
    return {"Authorization": f"Bearer {key}"} if key else {}


def _extract_price(market: dict) -> float:
    price = market.get("last_price_dollars") or market.get("previous_yes_bid_dollars") or 0
    return float(price)


def _is_thesis_relevant(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in THESIS_KEYWORDS)


def _dedup_similar(markets: list, max_shared_words: int = 4) -> list:
    """Drop near-duplicate titles, keeping higher volume first."""
    kept = []
    for m in markets:
        words = set(m["title"].lower().split())
        duplicate = any(
            len(words & set(k["title"].lower().split())) > max_shared_words
            for k in kept
        )
        if not duplicate:
            kept.append(m)
    return kept


@st.cache_data(ttl=120)
def fetch_kalshi_markets() -> list:
    """Fetch crisis-relevant markets from Kalshi via events endpoint."""
    try:
        r = requests.get(
            f"{KALSHI_API}/events",
            params={"status": "open", "with_nested_markets": "true", "limit": 100},
            headers=_kalshi_headers(),
            timeout=10,
        )
        r.raise_for_status()
        events = r.json().get("events", [])
        if not events:
            return [{"source": "kalshi", "error": "no open events returned"}]

        def _best_market(evt):
            markets = evt.get("markets", [])
            if not markets:
                return None
            best = max(markets, key=lambda m: float(m.get("volume_fp", 0) or 0))
            vol = float(best.get("volume_fp", 0) or 0)
            price = _extract_price(best)
            return {
                "source":   "kalshi",
                "ticker":   best.get("ticker", ""),
                "title":    best.get("title", evt.get("title", "")),
                "yes_pct":  round(price * 100, 1),
                "volume":   vol,
                "category": evt.get("category", ""),
                "error":    None,
            }

        all_results = [r for evt in events if (r := _best_market(evt)) is not None]
        all_results.sort(key=lambda x: x["volume"], reverse=True)

        thesis = [m for m in all_results if _is_thesis_relevant(m["title"])]
        thesis = _dedup_similar(thesis)

        if len(thesis) >= MIN_THESIS_MARKETS:
            return thesis[:MAX_KALSHI]

        # Pad with top fallback (Economics/Financials) markets not already included
        fallback = [
            m for m in all_results
            if m["category"] in FALLBACK_KALSHI_CATEGORIES
            and m not in thesis
        ]
        combined = (thesis + fallback)[:MAX_KALSHI]
        return combined if combined else [{"source": "kalshi", "error": "no relevant markets"}]

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
                "limit": 100, "order": "volume", "ascending": "false",
            },
            timeout=10,
        )
        r.raise_for_status()
        events = r.json()
        if not events:
            return [{"source": "polymarket", "error": "no active events returned"}]

        def _yes_price(m):
            try:
                return float(json.loads(m.get("outcomePrices", '["0"]'))[0])
            except (json.JSONDecodeError, IndexError, ValueError):
                return 0

        candidates = []
        for evt in events:
            tags = evt.get("tags") or []
            tag_slugs = {t.get("slug", "") for t in tags} if isinstance(tags, list) and tags and isinstance(tags[0], dict) else set()
            if tag_slugs & POLY_EXCLUDE_TAGS:
                continue

            markets = evt.get("markets") or []
            open_markets = [m for m in markets if not m.get("closed") and m.get("outcomePrices")]
            if not open_markets or len(open_markets) > MAX_EVENT_MARKETS:
                continue

            best = max(open_markets, key=_yes_price)
            prices = json.loads(best.get("outcomePrices", '["0","1"]'))
            title = best.get("question", evt.get("title", ""))
            candidates.append({
                "source":  "polymarket",
                "title":   title,
                "yes_pct": round(float(prices[0]) * 100, 1),
                "volume":  float(evt.get("volume", 0) or 0),
                "error":   None,
            })

        # Split into thesis-relevant and fallback
        thesis = [m for m in candidates if _is_thesis_relevant(m["title"])]
        thesis = _dedup_similar(thesis)

        if len(thesis) >= MIN_THESIS_MARKETS:
            return thesis[:MAX_POLYMARKET]

        fallback = [m for m in candidates if m not in thesis]
        combined = (thesis + fallback)[:MAX_POLYMARKET]
        return combined if combined else [{"source": "polymarket", "error": "no relevant events"}]

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
