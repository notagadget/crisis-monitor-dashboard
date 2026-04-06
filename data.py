"""
data.py — external data fetching only.
All functions return plain Python types; no Streamlit calls here.
"""

from datetime import datetime
import pytz
import streamlit as st
import yfinance as yf

from config import PRICE_TICKERS, JETS_PUT, DEADLINE_ISO, DEADLINE_TZ


@st.cache_data(ttl=300)
def fetch_prices() -> dict[str, float]:
    """
    Fetch latest prices for all tracked tickers via yfinance.
    Returns a dict of {ticker: price}. Falls back to last known value on error.
    """
    try:
        data = yf.download(PRICE_TICKERS, period="1d", interval="1m", progress=False)
        return {t: float(data["Close"][t].iloc[-1]) for t in PRICE_TICKERS}
    except Exception:
        return {}


@st.cache_data(ttl=300)
def fetch_option_price() -> dict:
    """
    Fetch the JETS put price from config.JETS_PUT.
    Returns {"price": float|None, "source": "last"|"mid"|"bid"|None}.
    Tries lastPrice first, then bid/ask midpoint, then bid alone.
    """
    try:
        tk = yf.Ticker(JETS_PUT["underlying"])
        chain = tk.option_chain(JETS_PUT["expiry_date"])
        puts = chain.puts
        row = puts[puts["strike"] == float(JETS_PUT["strike"])]
        if not row.empty:
            r = row.iloc[0]
            last = float(r.get("lastPrice", 0) or 0)
            bid = float(r.get("bid", 0) or 0)
            ask = float(r.get("ask", 0) or 0)
            if last > 0:
                return {"price": last, "source": "last"}
            if bid > 0 and ask > 0:
                return {"price": round((bid + ask) / 2, 4), "source": "mid"}
            if bid > 0:
                return {"price": bid, "source": "bid"}
    except Exception:
        pass
    return {"price": None, "source": None}


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
