"""
data.py — external data fetching only.
All functions return plain Python types; no Streamlit calls here.
"""

from datetime import datetime
import math
import pytz
import streamlit as st
import yfinance as yf
import requests

from config import PRICE_TICKERS, OPTIONS_POSITIONS, DEADLINE_ISO, DEADLINE_TZ


@st.cache_data(ttl=300)
def fetch_prices() -> dict[str, float]:
    """
    Fetch latest prices for all tracked tickers via yfinance.
    Returns a dict of {ticker: price}. Falls back to last known value on error.
    """
    try:
        data = yf.download(PRICE_TICKERS, period="1d", interval="1m", progress=False)
        out = {}
        for t in PRICE_TICKERS:
            v = float(data["Close"][t].iloc[-1])
            if not math.isnan(v):
                out[t] = v
        return out
    except Exception:
        return {}


@st.cache_data(ttl=300)
def fetch_option_prices() -> dict:
    """
    Fetch live prices for all active options in OPTIONS_POSITIONS.
    Returns {option_symbol: {"price": float|None, "source": str|None}}.
    Tries lastPrice first, then bid/ask midpoint, then bid alone.
    """
    results = {}
    for opt in OPTIONS_POSITIONS:
        if not opt.get("active"):
            continue
        symbol = opt["option_symbol"]
        try:
            tk = yf.Ticker(opt["underlying"])
            chain = tk.option_chain(opt["expiry_date"])
            df = chain.puts if opt.get("option_type", "put") == "put" else chain.calls
            row = df[df["strike"] == float(opt["strike"])]
            if not row.empty:
                r = row.iloc[0]
                def _safe(key):
                    v = float(r.get(key, 0) or 0)
                    return v if not math.isnan(v) else 0.0
                last = _safe("lastPrice")
                bid  = _safe("bid")
                ask  = _safe("ask")
                if last > 0:
                    results[symbol] = {"price": last, "source": "last"}
                    continue
                if bid > 0 and ask > 0:
                    results[symbol] = {"price": round((bid + ask) / 2, 4), "source": "mid"}
                    continue
                if bid > 0:
                    results[symbol] = {"price": bid, "source": "bid"}
                    continue
        except Exception:
            pass
        results[symbol] = {"price": None, "source": None}
    return results


PORTWATCH_API = "https://portwatch.imf.org/api"
HORMUZ_PORT_ID = "IQUMQ"  # IMF PortWatch port code for Strait of Hormuz

@st.cache_data(ttl=3600)  # hourly — PortWatch updates daily
def fetch_portwatch_transits() -> dict:
    """
    Fetch recent daily vessel transit counts through the Strait of Hormuz
    from IMF PortWatch. Returns a dict with:
      - counts: list of {date: str, value: float} sorted oldest→newest
      - ma7: float | None  (7-day moving average of most recent 7 days)
      - latest: float | None
      - threshold: int (60 — thesis resolution level)
      - error: str | None
    """
    try:
        # PortWatch indicator: vessel_calls (daily transits)
        r = requests.get(
            f"{PORTWATCH_API}/portmonitor",
            params={
                "portid": HORMUZ_PORT_ID,
                "indicator": "vessel_calls",
                "frequency": "D",
                "limit": 30,
            },
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

        records = data.get("data", [])
        if not records:
            return {"counts": [], "ma7": None, "latest": None,
                    "threshold": 60, "error": "no data returned"}

        # Normalize — PortWatch returns [{date, value}] or similar
        counts = sorted(
            [{"date": d["date"], "value": float(d["value"])}
             for d in records if d.get("value") is not None],
            key=lambda x: x["date"]
        )

        latest = counts[-1]["value"] if counts else None
        recent7 = [c["value"] for c in counts[-7:]]
        ma7 = round(sum(recent7) / len(recent7), 1) if len(recent7) >= 3 else None

        return {
            "counts": counts,
            "ma7": ma7,
            "latest": latest,
            "threshold": 60,
            "error": None,
        }

    except Exception as e:
        return {"counts": [], "ma7": None, "latest": None,
                "threshold": 60, "error": str(e)[:80]}


def countdown_to_deadline() -> str:
    """Returns a human-readable 'Xd Yh Zm' string until the Iran ultimatum deadline."""
    try:
        tz = pytz.timezone(DEADLINE_TZ)
        deadline = tz.localize(datetime.fromisoformat(DEADLINE_ISO))
        now = datetime.now(tz=tz)
        diff = deadline - now
        if diff.total_seconds() <= 0:
            return "EXPIRED"
        d = diff.days
        h = diff.seconds // 3600
        m = (diff.seconds % 3600) // 60
        return f"{d}d {h}h {m}m"
    except Exception:
        return "—"
