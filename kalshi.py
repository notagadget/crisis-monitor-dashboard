"""
kalshi.py — Kalshi + Polymarket prediction market data.
Kalshi market data is public — no auth key needed for reads.
Base URL confirmed: https://api.elections.kalshi.com/trade-api/v2
"""

import json
import requests

KALSHI_API = "https://api.elections.kalshi.com/trade-api/v2"

# WTI range markets — we fetch specific strike tiers most relevant to thesis
# Scenario B: $85–100 (already there), Scenario C: $120–200
WTI_STRIKES = [120, 150, 180]   # fetch these three tiers

# Single binary markets (event_ticker → market_ticker)
KALSHI_BINARY_MARKETS = {
    "recession":        "KXRECSSNBER",       # US recession 2026 — verify ticker below
    "iran_deal":        "KXUSAIRANAGREEMENT", # Iran nuclear deal — verify ticker
}

POLYMARKET_SLUGS = {
    "hormuz_apr": "will-strait-of-hormuz-be-closed-on-april-30-2026",
}


def fetch_kalshi_markets(api_key: str = "") -> dict:
    """Fetch WTI range markets + binary markets. No auth needed."""
    results = {}

    # WTI range markets via event lookup
    wti_markets = _fetch_wti_range_markets()
    results["wti_range"] = wti_markets  # list of {strike, yes_pct, ticker}

    # Binary markets
    for key, ticker in KALSHI_BINARY_MARKETS.items():
        results[key] = _fetch_single_market(ticker)

    return results


def fetch_polymarket_odds() -> dict:
    results = {}
    for key, slug in POLYMARKET_SLUGS.items():
        results[key] = _fetch_polymarket(slug)
    return results


def format_markets_for_prompt(kalshi: dict, polymarket: dict) -> str:
    lines = ["PREDICTION MARKETS (live odds):"]

    # WTI range — show the implied distribution
    wti = kalshi.get("wti_range", [])
    if wti and not isinstance(wti, dict):
        lines.append("- Kalshi WTI 2026 max price odds:")
        for tier in wti:
            if not tier.get("error"):
                lines.append(f"    >${tier['strike']}: {tier['yes_pct']}% YES")
    else:
        lines.append("- Kalshi WTI range: unavailable")

    # Recession
    rec = kalshi.get("recession", {})
    if rec.get("error"):
        lines.append(f"- Kalshi US recession 2026: unavailable")
    else:
        lines.append(f"- Kalshi US recession 2026: {rec.get('yes_pct', '?')}% YES · {rec.get('title','')}")

    # Iran deal
    iran = kalshi.get("iran_deal", {})
    if iran.get("error"):
        lines.append(f"- Kalshi Iran deal: unavailable")
    else:
        lines.append(f"- Kalshi Iran nuclear deal: {iran.get('yes_pct', '?')}% YES")

    # Polymarket Hormuz
    pm = polymarket.get("hormuz_apr", {})
    if pm.get("error"):
        lines.append("- Polymarket Hormuz closed Apr 30: unavailable")
    else:
        lines.append(f"- Polymarket Hormuz closed Apr 30: {pm.get('yes_price', '?')}% YES")

    return "\n".join(lines)


def _fetch_wti_range_markets() -> list:
    """Fetch specific WTI strike tiers from the active KXWTIMAX-26DEC31 event."""
    results = []
    for strike in WTI_STRIKES:
        ticker = f"KXWTIMAX-26DEC31-T{strike}"
        try:
            r = requests.get(f"{KALSHI_API}/markets/{ticker}", timeout=8)
            if r.status_code == 404:
                results.append({"strike": strike, "error": "not found"})
                continue
            r.raise_for_status()
            m = r.json().get("market", {})
            yes_raw = float(m.get("yes_bid_dollars", 0))
            results.append({
                "strike": strike,
                "yes_pct": round(yes_raw * 100, 1),
                "ticker": ticker,
                "error": None,
            })
        except Exception as e:
            results.append({"strike": strike, "error": str(e)[:60]})
    return results


def _fetch_single_market(ticker: str) -> dict:
    """Fetch a single binary market by ticker."""
    try:
        r = requests.get(f"{KALSHI_API}/markets/{ticker}", timeout=8)
        if r.status_code == 404:
            return {"error": f"{ticker} not found"}
        r.raise_for_status()
        m = r.json().get("market", {})
        yes_raw = float(m.get("yes_bid_dollars", 0))
        return {
            "title":   m.get("title", ticker),
            "yes_pct": round(yes_raw * 100, 1),
            "ticker":  ticker,
            "error":   None,
        }
    except Exception as e:
        return {"error": str(e)[:80]}


def _fetch_polymarket(slug: str) -> dict:
    try:
        r = requests.get(f"https://gamma-api.polymarket.com/markets?slug={slug}", timeout=8)
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