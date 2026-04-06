"""
kalshi.py — Kalshi + Polymarket prediction market data.
All prices from last_price_dollars (0.0–1.0 scale → multiply by 100 for %).
"""

import json
import requests

KALSHI_API = "https://api.elections.kalshi.com/trade-api/v2"


def fetch_kalshi_markets() -> dict:
    return {
        "wti_range": _fetch_wti_markets(),
        "recession": _fetch_series_first("KXUSRECESSION", fallback_keyword="recession"),
        "iran_deal": _fetch_series_first("KXIRAN", fallback_keyword="iran"),
    }


def fetch_polymarket_odds() -> dict:
    return {"hormuz_apr": _fetch_polymarket_keyword("hormuz")}


def format_markets_for_prompt(kalshi: dict, polymarket: dict) -> str:
    lines = ["PREDICTION MARKETS (live odds):"]

    wti = kalshi.get("wti_range", [])
    if wti and not all(t.get("error") for t in wti):
        lines.append("- Kalshi WTI weekly range markets:")
        for m in wti:
            if not m.get("error"):
                lines.append(f"    {m['subtitle']}: {m['yes_pct']}% YES  [{m['ticker']}]")
    else:
        lines.append("- Kalshi WTI range: unavailable")

    for key, label in [("recession", "US recession"), ("iran_deal", "Iran")]:
        m = kalshi.get(key, {})
        if m.get("error"):
            lines.append(f"- Kalshi {label}: unavailable ({m['error']})")
        else:
            lines.append(f"- Kalshi {label}: {m.get('yes_pct','?')}% YES · {m.get('title','')}")

    pm = polymarket.get("hormuz_apr", {})
    if pm.get("error"):
        lines.append(f"- Polymarket Hormuz: unavailable ({pm['error']})")
    else:
        lines.append(f"- Polymarket Hormuz: {pm.get('yes_price','?')}% YES · {pm.get('title','')}")

    return "\n".join(lines)


def _fetch_wti_markets() -> list:
    """Fetch open WTI weekly markets by series_ticker=KXWTI."""
    try:
        r = requests.get(
            f"{KALSHI_API}/markets",
            params={"series_ticker": "KXWTI", "status": "open", "limit": 10},
            timeout=8,
        )
        r.raise_for_status()
        markets = r.json().get("markets", [])
        if not markets:
            return [{"error": "no open KXWTI markets"}]
        results = []
        for m in markets[:5]:  # cap at 5 most relevant
            price = float(m.get("last_price_dollars") or m.get("previous_yes_bid_dollars") or 0)
            results.append({
                "ticker":   m.get("ticker", ""),
                "subtitle": m.get("no_sub_title", m.get("title", "")),
                "yes_pct":  round(price * 100, 1),
                "floor":    m.get("floor_strike"),
                "error":    None,
            })
        return results
    except Exception as e:
        return [{"error": str(e)[:80]}]


def _fetch_series_first(series_ticker: str, fallback_keyword: str = "") -> dict:
    """Fetch the first open market for a given series. Falls back to keyword search."""
    try:
        r = requests.get(
            f"{KALSHI_API}/markets",
            params={"series_ticker": series_ticker, "status": "open", "limit": 3},
            timeout=8,
        )
        r.raise_for_status()
        markets = r.json().get("markets", [])
        if not markets:
            if fallback_keyword:
                return _search_market_by_keyword(fallback_keyword)
            return {"error": f"no open markets for {series_ticker}"}
        m = markets[0]
        price = float(m.get("last_price_dollars") or m.get("previous_yes_bid_dollars") or 0)
        return {
            "title":   m.get("title", series_ticker),
            "yes_pct": round(price * 100, 1),
            "ticker":  m.get("ticker", ""),
            "error":   None,
        }
    except Exception as e:
        return {"error": str(e)[:80]}


def _search_market_by_keyword(keyword: str) -> dict:
    """Last-resort keyword search across open markets."""
    try:
        r = requests.get(
            f"{KALSHI_API}/markets",
            params={"status": "open", "limit": 20},
            timeout=8,
        )
        r.raise_for_status()
        kw = keyword.lower()
        matches = [
            m for m in r.json().get("markets", [])
            if kw in m.get("title", "").lower() or kw in m.get("ticker", "").lower()
        ]
        if not matches:
            return {"error": f"no open market matching '{keyword}'"}
        m = matches[0]
        price = float(m.get("last_price_dollars") or m.get("previous_yes_bid_dollars") or 0)
        return {
            "title":   m.get("title", keyword),
            "yes_pct": round(price * 100, 1),
            "ticker":  m.get("ticker", ""),
            "error":   None,
        }
    except Exception as e:
        return {"error": str(e)[:80]}


def _fetch_polymarket_keyword(keyword: str) -> dict:
    try:
        r = requests.get(
            "https://gamma-api.polymarket.com/markets",
            params={"q": keyword, "active": "true", "limit": 10},
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            return {"error": "no polymarket results"}
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