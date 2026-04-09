"""
config.py — static constants only. Edit this file to update positions,
signals, waiting list entries, or calendar events. No logic here.
"""
# App Version Number
APP_VERSION = "v0.92"
LAST_UPDATED = "April 9, 2026"  # update manually or via Morning Sync

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
    "s1": 0,  # war risk premiums easing with ceasefire
    "s2": 0,  # curve flattening as oil retreats
    "s3": 1,  # TRIGGERED — stays, ceasefire is a diplomatic signal
    "s4": 1,  # TRIGGERED — ceasefire confirms pragmatist faction
    "s5": 0,  # unchanged
    "s6": 0,  # unchanged
    "s7": 1,  # crowding risk resolved with exit
    "s8": 1,  # TRIGGERED — ceasefire = resolution post equivalent
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
    "s1": "War risk premiums easing with ceasefire announcement. Shipping insurance declining.",
    "s2": "Oil retreating as ceasefire reduces immediate supply disruption risk. Backwardation flattening.",
    "s3": "TRIGGERED: Ceasefire = diplomatic resolution signal. China-Pakistan mediation active throughout.",
    "s4": "TRIGGERED: Ceasefire confirms pragmatist faction influence. Pezeshkian-aligned outcome.",
    "s5": "Ras Laffan structurally still closed. Selective Hormuz opening does not reopen LNG/helium routes.",
    "s6": "SPR release ongoing. No drawdown slowdown observed.",
    "s7": "Energy bull thesis unwinding with ceasefire — crowding risk resolved with exit.",
    "s8": "TRIGGERED: Ceasefire declared April 8 — resolution equivalent per exit rule.",
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
    {"pct": "30%", "color": "#126030", "name": "A — Resolution",
     "desc": "Ceasefire holds, Hormuz reopens conditionally. Iran reparations framework agreed.", "active": True},
    {"pct": "40%", "color": "#1a6bb0", "name": "B — Partial Resolution",
     "desc": "Ceasefire → stalled negotiations → toll regime. Partial Hormuz reopening.", "active": False},
    {"pct": "45%", "color": "#a81828", "name": "C — Escalation",
     "desc": "Ceasefire breaks down after Apr 22 expiry. Strikes resume. Hormuz fully closed.", "active": False},
]

DEADLINE_ISO = "2026-04-22T20:00:00"   # ET — ceasefire expiry
DEADLINE_TZ  = "America/Detroit"
USER_TZ      = "America/Detroit"       # Your local timezone for timestamps

# ── WAITING LIST ──────────────────────────────────────────────────────────────
# status options: ready | event | watching | patience
WAITING_LIST = [
    {
        "ticker": "XOM / CVX",
        "status": "patience",
        "when": "Wait Islamabad Apr 12",
        "cond": "Ceasefire pause \u2014 wait for Islamabad talks (Apr 12) outcome before entering energy longs.",
        "alloc": "$3,000",
    },
    {
        "ticker": "APD",
        "status": "watching",
        "when": "Ras Laffan Structural",
        "cond": "Ras Laffan LNG/helium still structurally closed. Ceasefire does not reopen helium routes.",
        "alloc": "$2,000",
    },
    {
        "ticker": "MOS / CF",
        "status": "watching",
        "when": "Supply Disruption",
        "cond": "Fertilizer supply disruption persists structurally even under ceasefire. Spring planting watch.",
        "alloc": "$2,000",
    },
    {
        "ticker": "USO calls",
        "status": "patience",
        "when": "Post-Ceasefire",
        "cond": "Wait for ceasefire breakdown confirmation. Do not buy vol on ambiguity.",
        "alloc": "$1,000\u20131,500",
    },
    {
        "ticker": "SLB",
        "status": "patience",
        "when": "Post-Ceasefire",
        "cond": "Wait for XOM/CVX drilling capex announcement as trigger. Ceasefire pause.",
        "alloc": "$2,000",
    },
    {
        "ticker": "GLD calls",
        "status": "watching",
        "when": "Technical",
        "cond": "Add calls on 2 consecutive closes above 100-day SMA. Check Apr 9 close.",
        "alloc": "$1,500",
    },
]

# ── CALENDAR ──────────────────────────────────────────────────────────────────
CALENDAR = [
    {"date": "Apr 10", "event": "CPI report — first post-war inflation read",            "crit": True},
    {"date": "Apr 12", "event": "Islamabad talks — Vance/Witkoff/Kushner first round",  "crit": True},
    {"date": "Apr 21", "event": "NOC earnings",                                          "crit": False},
    {"date": "Apr 22", "event": "Ceasefire expires — re-evaluate thesis",               "crit": True},
    {"date": "Apr 28", "event": "RTX earnings (before open)",                            "crit": False},
    {"date": "Apr 30", "event": "LIN earnings",                                          "crit": False},
]

# ── DAY SUMMARY ───────────────────────────────────────────────────────────────
# Update this dict each morning — it's the only manually-edited daily content
DAY_SUMMARY = {
    "label": "Day 41 - April 09, 2026",
    "body": (
        "Ceasefire holds Day 2. Thesis remains PAUSED with 4 signals TRIGGERED. Islamabad talks April 12 critical - breakdown would clear re-entry path. Dry powder $33,601 ready (E*Trade $13,908 + Fidelity $19,693). GLD watching for 100-day SMA breakout confirmation."
    ),
}