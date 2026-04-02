"""
kalshi.py — Kalshi + Polymarket prediction market data.
Kalshi market data is public — no auth key needed for reads.
Base URL: https://api.elections.kalshi.com/trade-api/v2

Ticker verification strategy:
  - WTI: search the KXWTI event series for active markets
  - Binary: search by keyword rather than hardcoded tickers
  - Polymarket: search by keyword slug pattern
"""

import json
import requests

KALSHI_API = "https://api.elections.kalshi.com/trade-api/v2"


# ── PUBLIC ENTRY POINTS ───────────────────────────────────────────────────────

def fetch_kalshi_markets() -> dict:
    results = {"wti_range": _fetch_wti_range_markets(),
               "recession": _search_market_by_keyword("recession 2026"),
               "iran_deal": _search_market_by_keyword("iran")}
    return results


def fetch_polymarket_odds() -> dict:
    results = {"hormuz_apr": _fetch_polymarket_keyword("hormuz")}
    return results


def format_markets_for_prompt(kalshi: dict, polymarket: dict) -> str:
    lines = ["PREDICTION MARKETS (live odds):"]

    wti = kalshi.get("wti_range", [])
    if wti and isinstance(wti, list) and not all(t.get("error") for t in wti):
        lines.append("- Kalshi WTI 2026 max price odds:")
        for tier in wti:
            if not tier.get("error"):
                lines.append(f"    >${tier['strike']}: {tier['yes_pct']}% YES  [{tier['ticker']}]")
    else:
        errs = [t.get("error","?") for t in wti] if isinstance(wti, list) else [str(wti)]
        lines.append(f"- Kalshi WTI range: unavailable ({errs[0]})")

    rec = kalshi.get("recession", {})
    if rec.get("error"):
        lines.append(f"- Kalshi US recession: unavailable ({rec['error']})")
    else:
        lines.append(f"- Kalshi US recession 2026: {rec.get('yes_pct','?')}% YES · {rec.get('title','')}")

    iran = kalshi.get("iran_deal", {})
    if iran.get("error"):
        lines.append(f"- Kalshi Iran: unavailable ({iran['error']})")
    else:
        lines.append(f"- Kalshi Iran market: {iran.get('yes_pct','?')}% YES · {iran.get('title','')}")

    pm = polymarket.get("hormuz_apr", {})
    if pm.get("error"):
        lines.append(f"- Polymarket Hormuz: unavailable ({pm['error']})")
    else:
        lines.append(f"- Polymarket Hormuz: {pm.get('yes_price','?')}% YES · {pm.get('title','')}")

    return "\n".join(lines)


# ── WTI RANGE ─────────────────────────────────────────────────────────────────

def _fetch_wti_range_markets() -> list:
    """
    Search Kalshi for active WTI markets, then probe known strike tiers.
    Falls back to direct ticker construction if search works.
    """
    # Step 1: find the active WTI event series
    try:
        r = requests.get(
            f"{KALSHI_API}/events",
            params={"series_ticker": "KXWTI", "status": "open", "limit": 5},
            timeout=8,
        )
        r.raise_for_status()
        events = r.json().get("events", [])
    except Exception as e:
        events = []

    # Step 2: from the event, get markets
    results = []
    strikes_wanted = [120, 150, 180]

    if events:
        event_ticker = events[0].get("event_ticker", "")
        for strike in strikes_wanted:
            ticker = f"{event_ticker}-T{strike}"
            result = _fetch_single_market(ticker)
            result["strike"] = strike
            results.append(result)
    else:
        # Fallback: try current year pattern directly
        for strike in strikes_wanted:
            ticker = f"KXWTIMAX-26DEC31-T{strike}"
            result = _fetch_single_market(ticker)
            result["strike"] = strike
            results.append(result)

    return results


# ── KEYWORD SEARCH ────────────────────────────────────────────────────────────

def _search_market_by_keyword(keyword: str) -> dict:
    """Search Kalshi markets by keyword, return the most relevant open one."""
    try:
        r = requests.get(
            f"{KALSHI_API}/markets",
            params={"status": "open", "limit": 10},
            timeout=8,
        )
        r.raise_for_status()
        markets = r.json().get("markets", [])
        kw = keyword.lower()
        matches = [
            m for m in markets
            if kw in m.get("title", "").lower() or kw in m.get("ticker", "").lower()
        ]
        if not matches:
            return {"error": f"no open market matching '{keyword}'"}
        m = matches[0]
        yes_raw = float(m.get("yes_bid", m.get("yes_bid_dollars", 0)) or 0)
        # yes_bid is in cents on some endpoints, dollars on others
        yes_pct = round(yes_raw * 100, 1) if yes_raw <= 1.0 else round(yes_raw, 1)
        return {
            "title":   m.get("title", keyword),
            "yes_pct": yes_pct,
            "ticker":  m.get("ticker", ""),
            "error":   None,
        }
    except Exception as e:
        return {"error": str(e)[:80]}


def _fetch_single_market(ticker: str) -> dict:
    try:
        r = requests.get(f"{KALSHI_API}/markets/{ticker}", timeout=8)
        if r.status_code == 404:
            return {"error": f"404 {ticker}"}
        r.raise_for_status()
        m = r.json().get("market", {})
        yes_raw = float(m.get("yes_bid", m.get("yes_bid_dollars", 0)) or 0)
        yes_pct = round(yes_raw * 100, 1) if yes_raw <= 1.0 else round(yes_raw, 1)
        return {
            "title":   m.get("title", ticker),
            "yes_pct": yes_pct,
            "ticker":  ticker,
            "error":   None,
        }
    except Exception as e:
        return {"error": str(e)[:80]}


# ── POLYMARKET ────────────────────────────────────────────────────────────────

def _fetch_polymarket_keyword(keyword: str) -> dict:
    """Search Polymarket gamma API by keyword, return best match."""
    try:
        r = requests.get(
            "https://gamma-api.polymarket.com/markets",
            params={"q": keyword, "active": "true", "limit": 10},
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            # Fallback: try direct slug
            return _fetch_polymarket_slug("will-strait-of-hormuz-be-closed-on-april-30-2026")
        kw = keyword.lower()
        matches = [m for m in data if kw in m.get("question", "").lower()]
        item = matches[0] if matches else data[0]
        prices = json.loads(item.get("outcomePrices", '["0","1"]'))
        return {
            "title":     item.get("question", keyword),
            "yes_price": round(float(prices[0]) * 100, 1),
            "error":     None,
        }
    except Exception as e:
        return {"error": str(e)[:80]}


def _fetch_polymarket_slug(slug: str) -> dict:
    try:
        r = requests.get(
            f"https://gamma-api.polymarket.com/markets",
            params={"slug": slug},
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            return {"error": "no market found"}
        prices = json.loads(data[0].get("outcomePrices", '["0","1"]'))
        return {
            "title":     data[0].get("question", slug),
            "yes_price": round(float(prices[0]) * 100, 1),
            "error":     None,
        }
    except Exception as e:
        return {"error": str(e)[:80]}
