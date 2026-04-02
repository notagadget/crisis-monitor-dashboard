"""
analysis.py — pure computation and prompt logic.
No Streamlit calls, no HTML rendering (that lives in components.py).
"""

import re
from config import POSITIONS, JETS_PUT, SIGNAL_NAMES, WAITING_LIST


# ── P&L ───────────────────────────────────────────────────────────────────────

def calc_pnl(ticker: str, current_price: float) -> float:
    """Dollar P&L for an equity position."""
    p = POSITIONS[ticker]
    return (current_price - p["entry"]) * p["shares"]


def calc_option_pnl(option_price: float | None) -> tuple[float | None, float | None]:
    """
    Returns (dollar_pnl, pct_pnl) for the JETS put position.
    Returns (None, None) if option_price is unavailable.
    """
    if option_price is None:
        return None, None
    basis = JETS_PUT["premium_paid"] * JETS_PUT["contracts"] * 100
    cur_val = option_price * JETS_PUT["contracts"] * 100
    pnl = cur_val - basis
    pct = (pnl / basis) * 100
    return pnl, pct


def thesis_totals(prices: dict, jets_pnl: float | None) -> dict:
    """Aggregate thesis P&L across all thesis equity positions + JETS puts."""
    equity_pnls = {t: calc_pnl(t, prices.get(t, POSITIONS[t]["entry"]))
                   for t, p in POSITIONS.items() if p["thesis"]}
    equity_total = sum(equity_pnls.values())
    jets = jets_pnl or 0.0
    return {
        "equity_rows": equity_pnls,
        "equity_total": equity_total,
        "jets_pnl": jets,
        "total": equity_total + jets,
    }


def legacy_totals(prices: dict) -> dict:
    """Aggregate legacy (non-thesis) P&L."""
    rows = {t: calc_pnl(t, prices.get(t, POSITIONS[t]["entry"]))
            for t, p in POSITIONS.items() if not p["thesis"]}
    return {"rows": rows, "total": sum(rows.values())}


# ── SIGNALS ───────────────────────────────────────────────────────────────────

def score_signals(signals: dict) -> dict:
    """
    Returns score metadata used by both the UI score box and the prompt.
    signals: {sid: 0|1|2}
    """
    triggered = sum(1 for v in signals.values() if v == 2)
    caution   = sum(1 for v in signals.values() if v == 1)

    if triggered >= 2:
        return {"n": triggered + caution, "lbl": "TRIGGERED / 8",
                "action": "Reduce energy longs 30–40%", "color": "#ff6070"}
    if triggered == 1:
        return {"n": triggered + caution, "lbl": "1 Triggered / 8",
                "action": "One triggered — prepare to reduce", "color": "#ffaa40"}
    if caution >= 2:
        return {"n": caution, "lbl": "Caution signals / 8",
                "action": "Amber — monitor, no exits yet", "color": "#ffaa40"}
    if caution == 1:
        return {"n": caution, "lbl": "Caution signals / 8",
                "action": "One caution — hold, watch closely", "color": "rgba(255,255,255,0.8)"}
    return {"n": 0, "lbl": "Triggered / 8",
            "action": "All clear — hold positions", "color": "#3dd880"}


# ── PROMPT ────────────────────────────────────────────────────────────────────

def build_prompt(prices: dict, jets_option_price: float | None, signals: dict) -> str:
    """
    Build the Claude analysis prompt from live data.
    Keeping this in one place makes prompt iteration fast.
    """
    sig_ctx = "\n".join(
        f"{i+1}. {SIGNAL_NAMES[sid]}: "
        f"{'TRIGGERED' if signals[sid] == 2 else 'CAUTION' if signals[sid] == 1 else 'CLEAR'}"
        for i, sid in enumerate(SIGNAL_NAMES)
    )

    jets_underlying = prices.get("JETS", "N/A")
    jets_opt_str = f"${jets_option_price:.2f}" if jets_option_price else "N/A (market closed)"

    wait_str = " · ".join(
        f"{w['ticker']} ({w['when'].lower()})" for w in WAITING_LIST
    )

    return f"""You are a geopolitical crisis trading analyst. Today is April 1, 2026.

THESIS POSITIONS (live prices):
- RTX:  ${prices.get('RTX', 'N/A')} (entry $185.84, stop $184) | Apr 28 earnings
- NOC:  ${prices.get('NOC', 'N/A')} (entry $678.35, stop $631) | Apr 21 earnings
- LIN:  ${prices.get('LIN', 'N/A')} (entry $495.85, stop $456) | Apr 30 earnings
- JETS $23 Jun20 puts 10×: underlying ${jets_underlying} | put {jets_opt_str} | paid $1.72 | stop JETS>$27
- VTIP: ${prices.get('VTIP', 'N/A')} (entry $49.935, stop $47.50)
- Dry powder: ~$16,500

LEGACY HOLDS (excluded from thesis eval):
- GLD 10sh: ${prices.get('GLD', 'N/A')} (entry $281.57) — hold
- VTV 10sh: ${prices.get('VTV', 'N/A')} (entry $132.06) — hold

MARCH 31 DEVELOPMENTS:
- S&P +2.91%, Nasdaq +3.83% — best day since May
- Pezeshkian "open to talks with guarantees" — UNCONFIRMED, state media disputed
- Trump NYPost: Hormuz "automatically opens" after US leaves
- RTX only +0.7% vs mkt +2.9% on peace-hope defense selloff
- JETS +4.2% — adversarial for puts; underlying near stop
- GLD +3.4% with equities — unusual, embedded inflation signal
- Hormuz physically closed · Iran struck Kuwaiti tanker · Polymarket 82% no-Hormuz by Apr 30

EXIT SIGNAL STATUS:
{sig_ctx}

WAITING LIST: {wait_str}

CRITICAL DATES: Good Friday Apr 4 (closed) · Iran ultimatum Apr 6 8pm ET

Respond with exactly 5 sections, under 70 words each:
1. SITUATION UPDATE
2. SIGNAL ASSESSMENT
3. POSITION ALERTS — focus on JETS stop proximity and RTX recovery
4. WAITING LIST — which entries are ready to execute now
5. KEY RISK before April 6"""


# ── AI OUTPUT RENDERER ────────────────────────────────────────────────────────

_TICKERS = r'\b(RTX|NOC|LIN|JETS|VTIP|GLD|VTV|XOM|CVX|SLB|MOS|APD|USO|CF)\b'
_SECTION = r'\d\.\s*(SITUATION UPDATE|SIGNAL ASSESSMENT|POSITION ALERTS|WAITING LIST|KEY RISK[^:\n]*):?'
_SECTION_HTML = (
    '<div style="font-family:IBM Plex Sans,sans-serif;font-size:10px;font-weight:700;'
    'color:#0b4580;text-transform:uppercase;letter-spacing:.5px;margin:12px 0 4px;'
    'padding-bottom:3px;border-bottom:1px solid #d0d5e0;">\\1</div>'
)

def render_ai_html(text: str) -> str:
    """Convert Claude's plain-text response to styled HTML for st.markdown."""
    h = re.sub(_SECTION, _SECTION_HTML, text)
    h = h.replace("TRIGGERED", '<span class="tag-d">TRIGGERED</span>')
    h = h.replace("CAUTION",   '<span class="tag-w">CAUTION</span>')
    h = h.replace("CLEAR",     '<span class="tag-g">CLEAR</span>')
    h = re.sub(_TICKERS,
               r'<span style="color:#b86800;font-weight:600;">\1</span>', h)
    h = re.sub(r'\$[\d,]+\.?\d*',
               r'<span style="color:#126030;font-weight:600;">\g<0></span>', h)
    h = h.replace("\n", "<br>")
    return h
