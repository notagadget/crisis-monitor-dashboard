"""
config.py — static constants only. Edit this file to update positions,
signals, waiting list entries, or calendar events. No logic here.
"""

# ── POSITIONS ─────────────────────────────────────────────────────────────────
# thesis: True = included in thesis P&L bucket
# stop: None = no hard stop set
POSITIONS = {
    "RTX":  {"shares": 10,  "entry": 185.84, "stop": 180.00, "type": "Equity", "thesis": True},
    "NOC":  {"shares": 2,   "entry": 678.35, "stop": 631.00, "type": "Equity", "thesis": True},
    "LIN":  {"shares": 6,   "entry": 495.85, "stop": 456.00, "type": "Equity", "thesis": True},
    "VTIP": {"shares": 40,  "entry": 49.935, "stop": 47.50,  "type": "Equity", "thesis": True},
    "GLD":  {"shares": 10,  "entry": 281.57, "stop": None,   "type": "Equity", "thesis": False},
    "VTV":  {"shares": 10,  "entry": 132.06, "stop": None,   "type": "Equity", "thesis": False},
}

# Options position — one structured dict keeps all option math in one place
JETS_PUT = {
    "contracts":         10,
    "strike":            23,
    "expiry_label":      "Jun 20 2026",
    "expiry_date":       "2026-06-18",      # yfinance chain date
    "option_symbol":     "JETS260618P00023000",
    "premium_paid":      1.72,              # per share
    "stop_underlying":   27.00,             # exit if JETS closes above this
    "underlying":        "JETS",
}

# Tickers to fetch from yfinance (underlying prices only)
PRICE_TICKERS = ["RTX", "NOC", "LIN", "VTIP", "GLD", "VTV", "JETS",
                 "XOM", "CVX", "APD", "USO", "MOS", "CF"]

# Cash / dry powder (update manually when deployed)
DRY_POWDER = 16_500

# ── EXIT SIGNALS ──────────────────────────────────────────────────────────────
# Default state: 0=clear, 1=caution, 2=triggered
# Update defaults here when a signal's status changes materially between sessions
SIGNAL_DEFAULTS = {
    "s1": 0,  # Shipping insurance declining
    "s2": 0,  # Futures curve flattening
    "s3": 1,  # Xi–Trump diplomatic signal      ← CAUTION
    "s4": 1,  # Iranian pragmatist signals       ← CAUTION
    "s5": 0,  # Linde/APD force majeure lifted
    "s6": 0,  # SPR drawdown slowing
    "s7": 1,  # Media maximum consensus          ← CAUTION
    "s8": 1,  # Trump resolution post            ← CAUTION
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
    "s1": "Lloyd's war risk premiums. Still elevated.",
    "s2": "Steep backwardation persists. Not triggered.",
    "s3": "Pakistan hosted talks · China 5-pt plan visible",
    "s4": "Pezeshkian 'open to talks' — unconfirmed but noted",
    "s5": "Qatar FM still active. No resumption yet.",
    "s6": "172M bbl release just started. 120 days to run.",
    "s7": "Energy bull thesis mainstream. Crowding risk.",
    "s8": "NYPost: 'won't be there much longer.' Hormuz 'auto-opens.'",
}

# ── SCENARIOS ─────────────────────────────────────────────────────────────────
SCENARIOS = [
    {"pct": "35%", "color": "#1a6bb0", "name": "B — Partial Resolution",
     "desc": "Convoy escorts resume. Brent $85–100. Prolonged elevated baseline.", "active": True},
    {"pct": "50%", "color": "#a81828", "name": "C — Escalation",
     "desc": "82nd Airborne positioned. Kharg op imminent. Brent $120–200.", "active": False},
    {"pct": "15%", "color": "#126030", "name": "A — Resolution",
     "desc": "Pezeshkian signal unconfirmed. Iran hardliners dominant. Unlikely.", "active": False},
]

DEADLINE_ISO = "2026-04-06T20:00:00"   # ET — Iran ultimatum
DEADLINE_TZ  = "US/Eastern"

# ── WAITING LIST ──────────────────────────────────────────────────────────────
# status options: ready | event | watching | patience
WAITING_LIST = [
    {"ticker": "XOM / CVX", "status": "ready",    "when": "✓ Enter This Week",
     "cond": "WTI $101–103 post-WSJ pullback. Limit order, split entry. Don't chase.",
     "alloc": "$3,000"},
    {"ticker": "APD",       "status": "event",    "when": "Near Ready",
     "cond": "Helium containers past storage window. Peace talk noise does NOT reopen Ras Laffan.",
     "alloc": "$2,000"},
    {"ticker": "USO calls", "status": "watching", "when": "Post Apr 6",
     "cond": "Too much whipsaw on diplomatic headlines pre-deadline.",
     "alloc": "$1,000–1,500"},
    {"ticker": "SLB",       "status": "patience", "when": "2–4 Weeks",
     "cond": "Wait for XOM/CVX drilling capex announcement as trigger.",
     "alloc": "$2,000"},
    {"ticker": "MOS / CF",  "status": "patience", "when": "30–60 Days",
     "cond": "~50% global urea/sulfur disrupted. Fertilizer repricing lag.",
     "alloc": "$2,000"},
    {"ticker": "GLD calls", "status": "patience", "when": "Technical",
     "cond": "Add calls only on 2 consecutive closes above 100-day SMA.",
     "alloc": "$1,500"},
]

# ── CALENDAR ──────────────────────────────────────────────────────────────────
CALENDAR = [
    {"date": "Apr 4",  "event": "Good Friday — market closed",      "crit": True},
    {"date": "Apr 6",  "event": "Iran ultimatum 8pm ET · set stops Thu", "crit": True},
    {"date": "Apr 21", "event": "NOC earnings",                      "crit": False},
    {"date": "Apr 28", "event": "RTX earnings (before open)",        "crit": False},
    {"date": "Apr 30", "event": "LIN earnings",                      "crit": False},
    {"date": "Jun 20", "event": "JETS puts expiry",                  "crit": False},
]

# ── DAY SUMMARY ───────────────────────────────────────────────────────────────
# Update this dict each morning — it's the only manually-edited daily content
DAY_SUMMARY = {
    "label": "Day 33 - April 02, 2026",
    "body": (
        "Four exit signals at caution/triggered levels signal potential inflection point. RTX recovering strongly from entry, NOC solid gains. JETS put protection holding value as underlying consolidates. Diplomatic noise increasing but unconfirmed."
    ),
}
