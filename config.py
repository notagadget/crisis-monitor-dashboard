"""
config.py — static constants only. Edit this file to update positions,
signals, waiting list entries, or calendar events. No logic here.
"""
# App Version Number
APP_VERSION = "v0.10"
LAST_UPDATED = "April 13, 2026"  # update manually or via Morning Sync

# Re-entry Signal Mode
THESIS_PAUSED = True   # False when active positions exist

# ── POSITIONS ─────────────────────────────────────────────────────────────────
# thesis: True = included in thesis P&L bucket
# stop: None = no hard stop set
POSITIONS = {
    "GLD":  {"shares": 10,  "entry": 414.57, "stop": None,   "type": "Equity", "thesis": False},
    "VTV":  {"shares": 10,  "entry": 194.16, "stop": None,   "type": "Equity", "thesis": False},
}

# Options positions — list of active option positions (add/remove dicts here)
# Each dict must include: label, contracts, strike, expiry_label, expiry_date,
# option_symbol, premium_paid, underlying, option_type ("put"|"call"), active
# Optional: stop_underlying
OPTIONS_POSITIONS = [
    # Example (currently empty — JETS puts closed Apr 8):
    # {
    #     "label":           "JETS puts",
    #     "contracts":       10,
    #     "strike":          23,
    #     "expiry_label":    "Jun 18 2026",
    #     "expiry_date":     "2026-06-18",
    #     "option_symbol":   "JETS260618P00023000",
    #     "premium_paid":    1.72,
    #     "stop_underlying": 27.00,
    #     "underlying":      "JETS",       # also add to PRICE_TICKERS if new
    #     "option_type":     "put",
    #     "active":          True,
    # }
]

# Tickers to fetch from yfinance (underlying prices only)
# Add option underlyings here when entering new options positions
PRICE_TICKERS = ["GLD", "VTV", "XOM", "CVX", "APD", "USO", "MOS", "CF"]

# Cash / dry powder (update manually when deployed)
DRY_POWDER = 33_601  # E*Trade 13,908 + Fidelity 19,693

# ── EXIT SIGNALS ──────────────────────────────────────────────────────────────
# Default state: 0=clear, 1=caution, 2=triggered
# Update defaults here when a signal's status changes materially between sessions
SIGNAL_DEFAULTS = {
    "s1": 1,  # CAUTION — blockade will push war risk premiums higher again
    "s2": 1,  # CAUTION — WTI/Brent rising; backwardation likely steepening
    "s3": 0,  # CLEAR — Islamabad failure reverses the diplomatic signal
    "s4": 0,  # CLEAR — Iran rejected all US nuclear terms; pragmatist faction failed
    "s5": 0,  # unchanged — Ras Laffan structurally still closed
    "s6": 0,  # unchanged — SPR release ongoing
    "s7": 1,  # CAUTION — energy bull consensus re-emerging with blockade
    "s8": 0,  # CLEAR — naval blockade is the opposite of a resolution post
}

SIGNAL_NAMES = {
    "s1": "Shipping insurance declining",
    "s2": "Futures curve flattening",
    "s3": "Xi–Trump diplomatic signal",
    "s4": "Iranian pragmatist signals",
    "s5": "Linde/APD force majeure lifted",
    "s6": "SPR drawdown slowing",
    "s7": "Media maximum consensus",
    "s8": "Trump resolution post",
}

SIGNAL_DESC = {
    "s1": "CAUTION: Naval blockade pushing war risk premiums higher. Shipping insurance costs reversing the post-ceasefire easing.",
    "s2": "CAUTION: WTI/Brent rising on blockade announcement. Backwardation likely steepening again as supply squeeze resumes.",
    "s3": "CLEAR: Islamabad talks failed Apr 12 after 21 hours — diplomatic signal reversed. Pakistan still attempting re-engagement.",
    "s4": "CLEAR: Iran rejected all US nuclear red lines in Islamabad. Pragmatist faction could not deliver. Ceasefire signal fully unwound.",
    "s5": "Ras Laffan structurally still closed. Ceasefire and blockade do not reopen LNG/helium routes.",
    "s6": "SPR release ongoing. No drawdown slowdown observed.",
    "s7": "CAUTION: Energy bull thesis re-emerging with naval blockade. Media consensus building again — crowding risk returning.",
    "s8": "CLEAR: Trump announced naval blockade Apr 13 — direct reversal of the ceasefire/resolution signal that triggered S8.",
}

SIGNAL_CLEAR = {
    "s1": "War risk premiums rise again — shipping insurance spiking post-ceasefire breakdown.",
    "s2": "Oil curve re-steepens into backwardation on renewed supply disruption.",
    "s3": "Diplomatic channel breaks down; Xi-Trump back-channel goes silent or hostile.",
    "s4": "Pragmatist faction loses influence; hardliners publicly reject ceasefire terms or reparations framework.",
    "s5": "Ras Laffan declares force majeure lifted; LNG/helium routes confirmed open.",
    "s6": "SPR drawdown slows or halts; IEA release ends.",
    "s7": "Energy bull thesis re-emerges in financial media; crowding risk returns.",
    "s8": "Trump posts escalation language or declares ceasefire failed; no extension announced.",
}

# ── SCENARIOS ─────────────────────────────────────────────────────────────────
# Ordered most-likely to least-likely
SCENARIOS = [
    {"pct": "55%", "color": "#a81828", "name": "C — Escalation",
     "desc": "Ceasefire expires Apr 22, naval blockade active, talks dead. Strikes resume. Hormuz fully closed.", "active": True},
    {"pct": "30%", "color": "#1a6bb0", "name": "B — Partial Resolution",
     "desc": "Pakistan re-engages, second round of talks. Stalemate → toll regime. Partial Hormuz reopening.", "active": False},
    {"pct": "15%", "color": "#126030", "name": "A — Resolution",
     "desc": "Iran accepts nuclear framework. Full Hormuz reopening. Requires reversal of current IRGC/government position.", "active": False},
]

DEADLINE_ISO = "2026-04-22T20:00:00"   # ET — ceasefire expiry
DEADLINE_TZ  = "America/Detroit"
USER_TZ      = "America/Detroit"       # Your local timezone for timestamps

# ── WAITING LIST ──────────────────────────────────────────────────────────────
# status options: ready | event | watching | patience
WAITING_LIST = [
    {"ticker": "XOM / CVX", "status": "watching", "when": "⚠ Watching — Don't Chase",
     "cond": "Blockade active — re-entry criteria met in principle. Set limit orders 2-3% below current levels ($148-149 XOM, $186-187 CVX). Do not chase the open spike.",
     "alloc": "$3,000"},
    {"ticker": "APD",       "status": "watching", "when": "Ras Laffan Structural",
     "cond": "Ras Laffan LNG/helium still structurally closed. Escalation strengthens the thesis. Independent of ceasefire outcome.",
     "alloc": "$2,000"},
    {"ticker": "MOS / CF",  "status": "watching", "when": "Supply Disruption",
     "cond": "Fertilizer supply disruption thesis strengthened by escalation. Spring planting watch remains active.",
     "alloc": "$2,000"},
    {"ticker": "USO calls", "status": "watching", "when": "⚠ Watching — Don't Chase",
     "cond": "Blockade active. Wait for vol to settle post-spike before buying calls. Confirmed closure only — wait for PortWatch data.",
     "alloc": "$1,000–1,500"},
    {"ticker": "SLB",       "status": "patience", "when": "Post-Ceasefire",
     "cond": "Wait for XOM/CVX drilling capex announcement as trigger. Not yet.",
     "alloc": "$2,000"},
    {"ticker": "GLD calls", "status": "ready", "when": "✓ Technical Trigger Met",
     "cond": "GLD at $435.36 — well above 100-day SMA (~$428). 2+ consecutive closes above SMA criterion met. Add on next pullback.",
     "alloc": "$1,500"},
]

# ── CALENDAR ──────────────────────────────────────────────────────────────────
CALENDAR = [
    {"date": "Apr 13", "event": "US naval blockade of Iranian ports begins — 10am ET", "crit": True},
    {"date": "Apr 21", "event": "NOC earnings",                                          "crit": False},
    {"date": "Apr 22", "event": "Ceasefire expires — hard re-entry decision point",     "crit": True},
    {"date": "Apr 28", "event": "RTX earnings (before open)",                            "crit": False},
    {"date": "Apr 30", "event": "LIN earnings",                                          "crit": False},
]

# ── DAY SUMMARY ───────────────────────────────────────────────────────────────
# Update this dict each morning — it's the only manually-edited daily content
DAY_SUMMARY = {
    "label": "Day 44 — April 13, 2026 — Escalation Confirmed",
    "body": (
        "Islamabad talks collapsed after 21 hours (Apr 12). US naval blockade of Iranian ports "
        "effective today. ~17 ships/day transiting Hormuz vs 130 baseline — well below 60-vessel "
        "re-entry threshold. Scenarios reset: C(Escalation) now modal at 55%. Signals S3/S4/S8 "
        "cleared; S1/S2/S7 flipped to caution. Re-entry criteria met in principle — "
        "do not chase today's spike. GLD calls technical trigger confirmed."
    ),
}