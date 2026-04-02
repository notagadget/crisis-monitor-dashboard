"""
kalshi.py — fetch prediction market data from Kalshi and Polymarket.
Returns normalized dicts ready for prompt injection and UI display.
"""

import requests

KALSHI_API = "https://api.elections.kalshi.com/trade-api/v2"

# ── MARKET SLUGS ──────────────────────────────────────────────────────────────
# These are the Kalshi event tickers most relevant to the Hormuz thesis.
# Update slugs here if Kalshi renames markets.
KALSHI_MARKETS = {
    "hormuz":     "HORMUZ-CLOSED-APR",      # Hormuz closure probability
    "iran_war":   "IRAN-US-WAR-2026",        # Iran conflict escalation
    "oil_range":  "OIL-MAY-RANGE",           # Oil price range (WTI May)
    "recession":  "RECESSION-2026",          # US recession odds
}

# Polymarket slugs (read via public API, no auth needed)
POLYMARKET_SLUGS = {
    "hormuz_apr": "will-strait-of-hormuz-be-closed-on-april-30-2026",
}


# ── PUBLIC INTERFACE ──────────────────────────────────────────────────────────

def fetch_kalshi_markets(api_key: str) -> dict:
    """
    Fetch all configured Kalshi markets.
    Returns dict of {market_key: market_data} where market_data has:
      - title: str
      - yes_price: float (0–100, probability %)
      - no_price: float
      - volume: int
      - status: str  (active | closed | settled)
      - error: str | None
    """
    results = {}
    for key, ticker in KALSHI_MARKETS.items():
        results[key] = _fetch_single_kalshi(api_key, ticker)
    return results


def fetch_polymarket_odds() -> dict:
    """
    Fetch Polymarket odds for Hormuz closure (public API, no auth).
    Returns dict with yes_price (%) or error.
    """
    results = {}
    for key, slug in POLYMARKET_SLUGS.items():
        results[key] = _fetch_polymarket(slug)
    return results


def format_markets_for_prompt(kalshi: dict, polymarket: dict) -> str:
    """Format prediction market data as a compact string for prompt injection."""
    lines = ["PREDICTION MARKETS (live odds):"]

    labels = {
        "hormuz":    "Kalshi — Hormuz closed Apr",
        "iran_war":  "Kalshi — Iran/US conflict escalation",
        "oil_range": "Kalshi — WTI oil price range",
        "recession": "Kalshi — US recession 2026",
    }

    for key, label in labels.items():
        d = kalshi.get(key, {})
        if d.get("error"):
            lines.append(f"- {label}: unavailable ({d['error']})")
        else:
            yes = d.get("yes_price", "?")
            vol = d.get("volume", 0)
            lines.append(f"- {label}: {yes}% YES · ${vol:,} volume")

    pm = polymarket.get("hormuz_apr", {})
    if pm.get("error"):
        lines.append(f"- Polymarket — Hormuz closed Apr 30: unavailable")
    else:
        lines.append(f"- Polymarket — Hormuz closed Apr 30: {pm.get('yes_price', '?')}% YES")

    return "\n".join(lines)


# ── INTERNAL ──────────────────────────────────────────────────────────────────

def _fetch_single_kalshi(api_key: str, ticker: str) -> dict:
    try:
        url = f"{KALSHI_API}/markets/{ticker}"
        r = requests.get(
            url,
            headers={"Authorization": f"Token {api_key}"},
            timeout=8,
        )
        if r.status_code == 404:
            return {"error": f"market {ticker} not found"}
        r.raise_for_status()
        m = r.json().get("market", {})
        return {
            "title":     m.get("title", ticker),
            "yes_price": round(m.get("yes_ask", 0) * 100, 1),
            "no_price":  round(m.get("no_ask", 0) * 100, 1),
            "volume":    m.get("volume", 0),
            "status":    m.get("status", "unknown"),
            "error":     None,
        }
    except Exception as e:
        return {"error": str(e)[:80]}


def _fetch_polymarket(slug: str) -> dict:
    try:
        # Polymarket gamma API — public, no auth
        url = f"https://gamma-api.polymarket.com/markets?slug={slug}"
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        data = r.json()
        if not data:
            return {"error": "no market found"}
        market = data[0]
        # outcomePrices is a JSON string like '["0.82", "0.18"]'
        import json
        prices = json.loads(market.get("outcomePrices", '["0","1"]'))
        yes_price = round(float(prices[0]) * 100, 1)
        return {
            "title":     market.get("question", slug),
            "yes_price": yes_price,
            "volume":    int(float(market.get("volume", 0))),
            "error":     None,
        }
    except Exception as e:
        return {"error": str(e)[:80]}
