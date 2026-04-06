"""
analysis.py — pure computation and prompt logic.
No Streamlit calls, no HTML rendering (that lives in components.py).
"""

import re
from datetime import date, datetime
from config import POSITIONS, JETS_PUT, SIGNAL_NAMES, SIGNAL_DESC, WAITING_LIST, DEADLINE_ISO


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

def capital_summary(prices: dict, jets_option_price: float | None, thesis: dict) -> dict:
    """
    Returns total capital deployed across thesis positions and overall % P&L.
    Excludes legacy holds and dry powder.
    """
    equity_cost = sum(
        POSITIONS[t]["entry"] * POSITIONS[t]["shares"]
        for t in POSITIONS if POSITIONS[t]["thesis"]
    )
    jets_cost = JETS_PUT["premium_paid"] * JETS_PUT["contracts"] * 100
    total_deployed = equity_cost + jets_cost
    total_pnl = thesis["total"]
    pct = (total_pnl / total_deployed) * 100 if total_deployed else 0
    return {
        "deployed": total_deployed,
        "pnl": total_pnl,
        "pct": pct,
    }

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


# ── DAILY ANALYSIS PROMPT ─────────────────────────────────────────────────────

def build_prompt(prices: dict, jets_option_price: float | None,
                 signals: dict, markets_str: str = "",
                 jets_option_source: str | None = None) -> str:
    """
    Build the Claude analysis prompt from live data.
    markets_str: formatted prediction market string from kalshi.format_markets_for_prompt()
    """
    sig_ctx = "\n".join(
        f"{i+1}. {SIGNAL_NAMES[sid]}: "
        f"{'TRIGGERED' if signals[sid] == 2 else 'CAUTION' if signals[sid] == 1 else 'CLEAR'}"
        for i, sid in enumerate(SIGNAL_NAMES)
    )

    jets_underlying = prices.get("JETS", "N/A")
    _src = f" ({jets_option_source})" if jets_option_source and jets_option_source != "last" else ""
    jets_opt_str = f"${jets_option_price:.2f}{_src}" if jets_option_price else "N/A (market closed)"

    wait_str = " · ".join(
        f"{w['ticker']} ({w['when'].lower()})" for w in WAITING_LIST
    )

    markets_section = f"\n{markets_str}\n" if markets_str else ""

    return f"""You are a geopolitical crisis trading analyst. Today is {date.today().strftime('%B %d, %Y')}.

THESIS POSITIONS (live prices):
- RTX:  ${prices.get('RTX', 'N/A')} (entry $185.84, stop $184) | Apr 28 earnings
- NOC:  ${prices.get('NOC', 'N/A')} (entry $678.35, stop $631) | Apr 21 earnings
- LIN:  ${prices.get('LIN', 'N/A')} (entry $495.85, stop $456) | Apr 30 earnings
- JETS ${JETS_PUT["strike"]} {datetime.strptime(JETS_PUT["expiry_date"], "%Y-%m-%d").strftime("%b%-d")} puts {JETS_PUT["contracts"]}×: underlying ${jets_underlying} | put {jets_opt_str} | paid ${JETS_PUT["premium_paid"]} | stop JETS>${JETS_PUT["stop_underlying"]}
- VTIP: ${prices.get('VTIP', 'N/A')} (entry $49.935, stop $47.50)
- Dry powder: ~$16,500

LEGACY HOLDS (excluded from thesis eval):
- GLD 10sh: ${prices.get('GLD', 'N/A')} (entry ${POSITIONS['GLD']['entry']}) — hold
- VTV 10sh: ${prices.get('VTV', 'N/A')} (entry ${POSITIONS['VTV']['entry']}) — hold
{markets_section}
EXIT SIGNAL STATUS:
{sig_ctx}

WAITING LIST: {wait_str}

CRITICAL DATES: Iran ultimatum {datetime.fromisoformat(DEADLINE_ISO).strftime("%b %-d")} 8pm ET

Respond with exactly 5 sections, under 70 words each:
1. SITUATION UPDATE
2. SIGNAL ASSESSMENT
3. POSITION ALERTS — focus on JETS stop proximity and RTX recovery
4. WAITING LIST — which entries are ready to execute now
5. KEY RISK before {datetime.fromisoformat(DEADLINE_ISO).strftime("%B %-d")}"""


# ── MORNING SYNC PROMPT (MERGED) ──────────────────────────────────────────────

def build_sync_prompt(prices: dict, jets_option_price: float | None,
                      current_signals: dict, markets_str: str,
                      jets_option_source: str | None = None) -> str:
    """
    Combined morning sync prompt: Claude returns structured JSON with
    config patches AND a full intelligence brief + updated scenario probabilities.

    JSON fields:
      - day_summary_label: str
      - day_summary_body: str (plain text, no HTML, ≤60 words)
      - signal_suggestions: {sid: {suggested: 0|1|2, reason: str}}
      - waiting_list_suggestions: [{ticker, suggested_status, suggested_when, reason}]
      - scenario_probabilities: {A: int, B: int, C: int}  (must sum to 100)
      - scenario_rationale: str  (≤40 words explaining the probability shift, if any)
      - ai_brief: str  (the 5-section intelligence brief, same format as standalone analysis)
      - key_insight: str (1 sentence)
    """
    today = date.today().strftime("%B %d, %Y")
    _src = f" ({jets_option_source})" if jets_option_source and jets_option_source != "last" else ""
    jets_str = f"${jets_option_price:.2f}{_src}" if jets_option_price else "market closed"

    sig_ctx = "\n".join(
        f'  "{sid}": {{"current": {current_signals[sid]}, '
        f'"name": "{SIGNAL_NAMES[sid]}", "desc": "{SIGNAL_DESC[sid]}"}}'
        for sid in SIGNAL_NAMES
    )

    wait_ctx = "\n".join(
        f'  {{"ticker": "{w["ticker"]}", "current_status": "{w["status"]}", '
        f'"cond": "{w["cond"]}"}}'
        for w in WAITING_LIST
    )

    # Format prices as plain strings to avoid JSON escape issues
    def px(t): return str(round(prices[t], 2)) if t in prices else 'N/A'

    return f"""You are a geopolitical crisis trading analyst. Today is {today}.
    Produce a single JSON response combining a morning briefing AND a full intelligence brief.

    IMPORTANT: In your JSON response, do NOT use backslashes except for standard JSON escapes (\", \\, \n, \t). Do not escape dollar signs. Write dollar amounts as plain text, e.g. "$185.84" not "\$185.84".

    CURRENT LIVE PRICES:
    - RTX: {px('RTX')} (entry 185.84, stop 184) | Apr 28 earnings
    - NOC: {px('NOC')} (entry 678.35, stop 631) | Apr 21 earnings
    - LIN: {px('LIN')} (entry 495.85, stop 456) | Apr 30 earnings
    - JETS underlying: {px('JETS')} | put last: {jets_str} | paid 1.72 | stop JETS above 27
    - VTIP: {px('VTIP')} (entry 49.935, stop 47.50)
    - GLD: {px('GLD')} (entry {POSITIONS['GLD']['entry']}) | VTV: {px('VTV')} (entry {POSITIONS['VTV']['entry']})
    - Dry powder: approximately 16500

{markets_str}

CURRENT EXIT SIGNALS (0=clear, 1=caution, 2=triggered):
{sig_ctx}

WAITING LIST (current status):
{wait_ctx}

THESIS CONTEXT:
Operation Epic Fury (Feb 28): US/Israel struck Iran, Hormuz closed (~20% global oil).
Pezeshkian "open to talks" signal unconfirmed, disputed by Iranian state media.
White House said Hormuz reopening is NOT a core objective of the operation.
New supreme leader Mojtaba Khamenei: Hormuz leverage "must continue to be used."
Exit rule: 2+ signals triggered = reduce energy longs 30-40%.

BASELINE SCENARIO PROBABILITIES (update based on latest signals + prediction markets):
- A (Full resolution, Brent <$85): currently 15%
- B (Partial resolution / convoy escorts, Brent $85–100): currently 50%
- C (Escalation / Kharg strike, Brent $120–200): currently 35%

AI BRIEF FORMAT — for the ai_brief field, write exactly 5 sections, each under 70 words:
1. SITUATION UPDATE
2. SIGNAL ASSESSMENT
3. POSITION ALERTS — focus on JETS stop proximity and RTX recovery
4. WAITING LIST — which entries are ready to execute now
5. KEY RISK before {datetime.fromisoformat(DEADLINE_ISO).strftime("%B %-d")}

Respond ONLY with valid JSON, no preamble, no markdown fences:
{{
  "day_summary_label": "Day N - {today}",
  "day_summary_body": "plain text under 60 words",
  "signal_suggestions": {{
    "s1": {{"suggested": 0, "reason": "one sentence"}},
    "s2": {{"suggested": 0, "reason": "one sentence"}},
    "s3": {{"suggested": 1, "reason": "one sentence"}},
    "s4": {{"suggested": 1, "reason": "one sentence"}},
    "s5": {{"suggested": 0, "reason": "one sentence"}},
    "s6": {{"suggested": 0, "reason": "one sentence"}},
    "s7": {{"suggested": 1, "reason": "one sentence"}},
    "s8": {{"suggested": 1, "reason": "one sentence"}}
  }},
  "waiting_list_suggestions": [
    {{"ticker": "XOM / CVX", "suggested_status": "ready", "suggested_when": "✓ Enter This Week", "reason": "one sentence"}}
  ],
  "scenario_probabilities": {{"A": 15, "B": 50, "C": 35}},
  "scenario_rationale": "one sentence explaining any probability shift vs baseline",
  "ai_brief": "1. SITUATION UPDATE:\\n<text>\\n\\n2. SIGNAL ASSESSMENT:\\n<text>\\n\\n3. POSITION ALERTS:\\n<text>\\n\\n4. WAITING LIST:\\n<text>\\n\\n5. KEY RISK:\\n<text>",
  "key_insight": "single most important thing the trader needs to know right now"
}}"""


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