"""
config.py — static constants only. Edit this file to update positions,
signals, waiting list entries, or calendar events. No logic here.
"""
# App Version Number
APP_VERSION = "v0.7"
LAST_UPDATED = "April 5, 2026"  # update manually or via Morning Sync


# ── POSITIONS ─────────────────────────────────────────────────────────────────
# thesis: True = included in thesis P&L bucket
# stop: None = no hard stop set
POSITIONS = {
    "RTX":  {"shares": 10,  "entry": 185.84, "stop": 184.00, "type": "Equity", "thesis": True},
    "NOC":  {"shares": 2,   "entry": 678.35, "stop": 631.00, "type": "Equity", "thesis": True},
    "LIN":  {"shares": 6,   "entry": 495.85, "stop": 456.00, "type": "Equity", "thesis": True},
    "VTIP": {"shares": 40,  "entry": 49.935, "stop": 47.50,  "type": "Equity", "thesis": True},
    "GLD":  {"shares": 10,  "entry": 414.57, "stop": None,   "type": "Equity", "thesis": False},
    "VTV":  {"shares": 10,  "entry": 194.16, "stop": None,   "type": "Equity", "thesis": False},
}

# Options position — one structured dict keeps all option math in one place
JETS_PUT = {
    "contracts":         10,
    "strike":            23,
    "expiry_label":      "Jun 18 2026",
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
    "s1": 1,  # Shipping insurance declining   ← CAUTION (UNSC vote today; escorts possible)
    "s2": 0,  # Futures curve flattening        (steep backwardation persists; WTI>Brent inversion)
    "s3": 2,  # Xi–Trump diplomatic signal      ← TRIGGERED (China blocked ships Mar 27; China-Pakistan 5-pt plan; active mediation)
    "s4": 1,  # Iranian pragmatist signals       ← CAUTION (Pezeshkian "open to talks" but state media contradicts; Iran rejected US proposal)
    "s5": 0,  # Linde/APD force majeure lifted  (Qatar FM active; no Ras Laffan resumption)
    "s6": 0,  # SPR drawdown slowing            (400M bbl release ongoing; ~120 days)
    "s7": 1,  # Media maximum consensus          ← CAUTION (energy bull very mainstream; WTI inversion coverage)
    "s8": 1,  # Trump resolution post            ← CAUTION (3rd deadline Apr 6 not yet passed; if no action → TRIGGERED)
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
    "s1": "UNSC vote Apr 4 on 'defensive force' for Hormuz escorts — if passes, war risk premiums could ease rapidly.",
    "s2": "WTI $110.85 now ABOVE Brent $108.95 — historic inversion; record front-month backwardation. Curve not flattening.",
    "s3": "TRIGGERED: China blocked 2 ships Mar 27; China-Pakistan 5-pt peace plan published; active mediation underway.",
    "s4": "Pezeshkian 'open to talks' BUT Iran rejected US proposal, demanding Hormuz sovereignty recognition.",
    "s5": "Qatar FM active. No Ras Laffan LNG/helium resumption. Selective Hormuz opening excludes US-linked vessels.",
    "s6": "400M bbl SPR release running (~120 days). IEA warns Apr disruptions 2× worse than March.",
    "s7": "WTI/Brent inversion now mainstream financial news. Energy bull thesis crowded.",
    "s8": "Trump set Tue 8pm ET deadline; named power plants + bridges. Not a soft extension.",}

# ── SCENARIOS ─────────────────────────────────────────────────────────────────
# Ordered most-likely to least-likely
SCENARIOS = [
    {"pct": "45%", "color": "#a81828", "name": "C — Escalation",
     "desc": "Trump named power plants + bridges for Tue. F-15E downed, A-10 hit. Polymarket 96% forces enter by Apr 30.", "active": True},
    {"pct": "40%", "color": "#1a6bb0", "name": "B — Partial Resolution",
     "desc": "Toll regime functioning. 53 transits last week. Oman-Iran talks underway.", "active": False},
    {"pct": "15%", "color": "#126030", "name": "A — Resolution",
     "desc": "Iran demanding reparations + toll fees before reopening. Hardliners dominant.", "active": False},
]

DEADLINE_ISO = "2026-04-08T20:00:00"   # ET — Iran ultimatum
DEADLINE_TZ  = "America/Detroit"

# ── WAITING LIST ──────────────────────────────────────────────────────────────
# status options: ready | event | watching | patience
WAITING_LIST = [
    {"ticker": "XOM / CVX", "status": "event", "when": "Post-Tue Strike",
     "cond": "If infra strike confirmed Tue: enter at Mon open. WTI already $113+, don't chase before.",
     "alloc": "$3,000"},
    {"ticker": "APD",       "status": "event",    "when": "Near Ready",
     "cond": "Helium containers past storage window. Selective Hormuz opening does NOT reopen Ras Laffan for LNG/helium.",
     "alloc": "$2,000"},
    {"ticker": "MOS / CF",  "status": "event",    "when": "Elevated Priority",
     "cond": "Iran toll legislation + fertilizer UN exemption is a band-aid. Spring planting window creating urgency.",
     "alloc": "$2,000"},
    {"ticker": "USO calls", "status": "watching", "when": "Post Apr 6",
     "cond": "WTI $111 already prices partial escalation. Calls expensive. Wait for vol crush or Kharg strike confirmation.",
     "alloc": "$1,000–1,500"},
    {"ticker": "SLB",       "status": "patience", "when": "2–4 Weeks",
     "cond": "Wait for XOM/CVX drilling capex announcement as trigger.",
     "alloc": "$2,000"},
    {"ticker": "GLD calls", "status": "patience", "when": "Technical",
     "cond": "Add calls only on 2 consecutive closes above 100-day SMA.",
     "alloc": "$1,500"},
]

# ── CALENDAR ──────────────────────────────────────────────────────────────────
CALENDAR = [
    {"date": "Apr 4",  "event": "Good Friday — market closed · UNSC Hormuz force vote", "crit": True},
    {"date": "Apr 6/8", "event": "Trump Tue 8pm ET deadline — power plants + bridges", "crit": True},
    {"date": "Apr 7",  "event": "EIA Short-Term Energy Outlook",                         "crit": False},
    {"date": "Apr 10", "event": "CPI report — first post-war inflation read",            "crit": False},
    {"date": "Apr 21", "event": "NOC earnings",                                          "crit": False},
    {"date": "Apr 28", "event": "RTX earnings (before open)",                            "crit": False},
    {"date": "Apr 30", "event": "LIN earnings",                                          "crit": False},
    {"date": "Jun 18", "event": "JETS puts expiry",                                      "crit": False},
]

# ── DAY SUMMARY ───────────────────────────────────────────────────────────────
# Update this dict each morning — it's the only manually-edited daily content
DAY_SUMMARY = {
    "label": "Day 34 — April 3, 2026",
    "body": (
        "Signal 3 upgrades to TRIGGERED: China-Pakistan actively mediating, China blocked ships Mar 27. "
        "WTI $111 now above Brent $108.95 — historic inversion signaling extreme prompt-supply stress. "
        "UNSC votes today on defensive force for Hormuz escorts; Russia/China veto likely. "
        "Iran rejected US proposal, demanding Hormuz sovereignty recognition — Scenario A now requires a toll regime, not unconditional opening. "
        "With 1 triggered + 3 caution: PREPARE TO REDUCE if Apr 6 passes without action (S8 → TRIGGERED = 2 total)."
    ),
}