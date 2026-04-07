# Implementation Plan: Cache, Option Data, and Stale Date Fixes

## Overview
Three focused fixes: (1) prediction market cache improvements, (2) richer JETS option data, (3) dynamic dates in AI prompts.

---

## Issue 1: Stale Prediction Market Data

### Problem
- `kalshi.py` lines 43 and 84: `@st.cache_data(ttl=600)` caches error responses for 10 minutes
- No manual refresh mechanism outside Morning Sync
- 10 minutes too long for active trading

### Implementation

**File: `kalshi.py`**

**Step 1a — Reduce TTL from 600s to 120s on both decorators.**
- Line 43: `@st.cache_data(ttl=600)` → `@st.cache_data(ttl=120)`
- Line 84: `@st.cache_data(ttl=600)` → `@st.cache_data(ttl=120)`

**Step 1b — Clear cache on error responses.**

The cleanest Streamlit pattern: after calling the cached function, check for errors and call `.clear()` if found. This avoids restructuring the functions.

In `app.py`, after lines 83-84 where `kalshi_data` and `poly_data` are fetched, add error-checking logic:

```python
kalshi_data = fetch_kalshi_markets() if KALSHI_KEY else []
if kalshi_data and any(m.get("error") for m in kalshi_data):
    fetch_kalshi_markets.clear()

poly_data = fetch_polymarket_odds()
if poly_data and any(m.get("error") for m in poly_data):
    fetch_polymarket_odds.clear()
```

This means: the current request still gets the error result (so the UI can display it), but the next page load will re-fetch instead of serving the cached error.

The same pattern should be applied in the Morning Sync block (app.py lines 143-145) where markets are re-fetched.

**Step 1c — Add a manual refresh button.**

In `app.py`, near line 82 (before the prediction markets fetch), add a small refresh button:

```python
if st.button("🔄", key="refresh_markets", help="Force refresh prediction markets"):
    fetch_kalshi_markets.clear()
    fetch_polymarket_odds.clear()
    st.rerun()
```

Place this button inline near the markets strip, or in a small column next to the MARKETS label in `components.py`. The simplest approach: add it right before the `prediction_markets_html` call on line 106, in a narrow column layout.

### Files changed
- `kalshi.py`: Lines 43, 84 (TTL values only)
- `app.py`: Lines 82-86 (add cache-clear on error), ~line 106 (add refresh button)

---

## Issue 2: JETS Put Option Data Unreliable

### Problem
- `data.py` `fetch_option_price()` (lines 27-42) uses only `lastPrice` which can be stale for illiquid options
- Returns bare `None` on any error with no diagnostics
- `None` gets cached for 5 minutes

### Implementation

**File: `data.py`**

**Step 2a — Change return type from `float | None` to a dict.**

Replace the current `fetch_option_price()` with a version that returns a richer result:

```python
@st.cache_data(ttl=300)
def fetch_option_price() -> dict:
    """
    Fetch JETS put price with quality indicator.
    Returns: {"price": float|None, "source": "last"|"mid"|"bid"|None, "status": str}
    """
    try:
        tk = yf.Ticker(JETS_PUT["underlying"])
        chain = tk.option_chain(JETS_PUT["expiry_date"])
        puts = chain.puts
        row = puts[puts["strike"] == float(JETS_PUT["strike"])]
        if row.empty:
            return {"price": None, "source": None, "status": "strike not found"}

        last = float(row["lastPrice"].iloc[0])
        bid = float(row["bid"].iloc[0]) if "bid" in row.columns else 0
        ask = float(row["ask"].iloc[0]) if "ask" in row.columns else 0

        # Prefer lastPrice if it looks reasonable (non-zero)
        if last > 0:
            return {"price": last, "source": "last", "status": "ok"}

        # Fall back to midpoint of bid/ask
        if bid > 0 and ask > 0:
            mid = round((bid + ask) / 2, 2)
            return {"price": mid, "source": "mid", "status": "ok"}

        # Fall back to bid alone
        if bid > 0:
            return {"price": bid, "source": "bid", "status": "ok"}

        return {"price": None, "source": None, "status": "no price data"}
    except Exception as e:
        return {"price": None, "source": None, "status": f"error: {str(e)[:60]}"}
```

**Step 2b — Clear cache on failure.**

In `app.py`, after calling `fetch_option_price()` (line 75), add:

```python
option_result = fetch_option_price()
option_price = option_result["price"]
option_source = option_result.get("source")
if option_price is None:
    fetch_option_price.clear()
```

**Step 2c — Update all callers of `fetch_option_price()`.**

There are exactly 3 call sites that use the return value:

1. **`app.py` line 75**: `option_price = fetch_option_price()` — change to unpack the dict as shown above.

2. **`app.py` line 76**: `opt_pnl, opt_pct = calc_option_pnl(option_price)` — no change needed, `option_price` is still `float | None`.

3. **`components.py` `jets_card_html()`** (line 202): Currently receives `option_price` as a float. Optionally pass `option_source` to show a small indicator (e.g., "(mid)" or "(bid)") next to the price. This is a minor UI enhancement:
   - Add an `option_source: str | None = None` parameter to `jets_card_html()`
   - If source is "mid" or "bid", append a small label like `<span style="font-size:8px;color:#5a6880;">(mid)</span>` next to the price display

4. **`analysis.py` lines 113, 169**: These format the option price for prompts. They already handle `None`. The `source` indicator could optionally be included in the prompt text (e.g., "put $1.85 (mid)") to give Claude context about data quality.

### Files changed
- `data.py`: Lines 27-42 (rewrite `fetch_option_price`)
- `app.py`: Line 75 (unpack dict), add cache-clear logic
- `components.py`: `jets_card_html` signature (optional source label)
- `analysis.py`: Lines 113, 169 (optionally include source in prompt)

---

## Issue 3: Hardcoded Stale Dates in AI Prompts

### Problem
Four hardcoded date references in `analysis.py` that are already stale:
- Line 127: `JETS $23 Jun20 puts` — should be `Jun18` per config
- Line 140: `Good Friday Apr 4 (closed)` — past date
- Line 147: `KEY RISK before April 6` — today IS April 6
- Line 225: Same `KEY RISK before April 6` in sync prompt

### Implementation

**File: `analysis.py`**

**Step 3a — Fix JETS expiry label (line 127).**

Replace the hardcoded `Jun20` with the config value. Change:
```
- JETS $23 Jun20 puts 10×
```
to:
```
- JETS ${JETS_PUT['strike']} {JETS_PUT['expiry_label']} puts {JETS_PUT['contracts']}×
```

This pulls from `config.py` where `expiry_label = "Jun 18 2026"`. The format will be slightly different ("Jun 18 2026" vs "Jun20") but more accurate. If you want the short format, derive it:
```python
from datetime import datetime
_exp = datetime.strptime(JETS_PUT["expiry_date"], "%Y-%m-%d")
_exp_short = _exp.strftime("%b%-d")  # "Jun18"
```

**Step 3b — Make CRITICAL DATES dynamic (line 140).**

Import `CALENDAR` from config and build the critical dates line dynamically:

```python
from config import CALENDAR
from datetime import date

def _critical_dates_str() -> str:
    today = date.today()
    # Filter to future or today's dates from CALENDAR that are critical
    upcoming = [ev for ev in CALENDAR if ev["crit"]]
    # Simple approach: show all critical dates (they're already in config)
    return " · ".join(f'{ev["date"]} ({ev["event"]})' for ev in upcoming[:3])
```

Replace line 140:
```
CRITICAL DATES: Good Friday Apr 4 (closed) · Iran ultimatum Apr 8 8pm ET
```
with:
```python
f"CRITICAL DATES: {_critical_dates_str()}"
```

Alternatively, since CALENDAR entries don't have parseable dates (they use strings like "Apr 4"), the simplest fix is to replace the hardcoded line with a reference to the deadline config:

```python
f"CRITICAL DATES: Iran ultimatum {DEADLINE_ISO[:10]} 8pm ET"
```

And remove the Good Friday reference since it has passed.

**Step 3c — Make "KEY RISK before" date dynamic (lines 147, 225).**

Replace the hardcoded section header. In both `build_prompt` (line 147) and `build_sync_prompt` (line 225):

Change:
```
5. KEY RISK before April 6
```
to:
```python
f"5. KEY RISK — next 48 hours"
```

Or reference the next critical deadline:

```python
from datetime import date, timedelta

_next_deadline = date.fromisoformat(DEADLINE_ISO[:10])
_deadline_label = _next_deadline.strftime("%B %-d")
...
f"5. KEY RISK before {_deadline_label}"
```

Using the Iran deadline from config (`DEADLINE_ISO = "2026-04-08T20:00:00"`) produces "KEY RISK before April 8" which is correct and dynamic.

This needs to be applied in two places:
- `build_prompt()` line 147
- `build_sync_prompt()` line 225

### Files changed
- `analysis.py`: Lines 127, 140, 147, 225 (dynamic date references)

---

## Implementation Sequence

1. **Issue 3 first** — purely string changes in `analysis.py`, zero risk of breaking data flow, immediate correctness improvement.
2. **Issue 1 second** — TTL changes + cache-clear pattern in `kalshi.py` and `app.py`. Low risk; the cache-clear pattern is well-documented in Streamlit.
3. **Issue 2 last** — changes the return type of `fetch_option_price()`, which requires updating multiple callers. Slightly higher coordination needed.

## Testing Notes

- Issue 1: Verify by temporarily breaking a Kalshi/Polymarket URL and confirming the error clears on next refresh (not cached for 2 min).
- Issue 2: Test during market-closed hours to verify the mid/bid fallback logic works. Check that `None` results are not cached.
- Issue 3: Verify prompt output with `print(build_prompt(...))` to confirm dates are correct.
