"""
analysis.py — pure computation and prompt logic.
No Streamlit calls, no HTML rendering (that lives in components.py).
"""

import re
from datetime import date, datetime
from config import POSITIONS, OPTIONS_POSITIONS, SIGNAL_NAMES, SIGNAL_DESC, WAITING_LIST, DEADLINE_ISO, DAY_SUMMARY, THESIS_PAUSED, SCENARIOS


# ── P&L ───────────────────────────────────────────────────────────────────────

def calc_pnl(ticker: str, current_price: float) -> float:
    """Dollar P&L for an equity position."""
    p = POSITIONS[ticker]
    return (current_price - p["entry"]) * p["shares"]


def calc_option_pnl(opt: dict, option_price: float | None) -> tuple[float | None, float | None]:
    """
    Returns (dollar_pnl, pct_pnl) for an options position dict.
    Returns (None, None) if option_price is unavailable.
    """
    if option_price is None:
        return None, None
    basis   = opt["premium_paid"] * opt["contracts"] * 100
    cur_val = option_price       * opt["contracts"] * 100
    pnl = cur_val - basis
    pct = (pnl / basis) * 100
    return pnl, pct


def thesis_totals(prices: dict, options_pnl_total: float = 0.0) -> dict:
    """Aggregate thesis P&L across all thesis equity positions + active options."""
    equity_pnls = {t: calc_pnl(t, prices.get(t, POSITIONS[t]["entry"]))
                   for t, p in POSITIONS.items() if p["thesis"]}
    equity_total = sum(equity_pnls.values())
    return {
        "equity_rows": equity_pnls,
        "equity_total": equity_total,
        "options_pnl": options_pnl_total,
        "total": equity_total + options_pnl_total,
    }


def legacy_totals(prices: dict) -> dict:
    """Aggregate legacy (non-thesis) P&L."""
    rows = {t: calc_pnl(t, prices.get(t, POSITIONS[t]["entry"]))
            for t, p in POSITIONS.items() if not p["thesis"]}
    return {"rows": rows, "total": sum(rows.values())}


def capital_summary(prices: dict, options_cost: float, thesis: dict) -> dict:
    """
    Returns total capital deployed across thesis equity + active options, and overall % P&L.
    Excludes legacy holds and dry powder.
    options_cost: sum of premium_paid * contracts * 100 for all active options.
    """
    equity_cost = sum(
        POSITIONS[t]["entry"] * POSITIONS[t]["shares"]
        for t in POSITIONS if POSITIONS[t]["thesis"]
    )
    total_deployed = equity_cost + options_cost
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

    When THESIS_PAUSED=True, signals read as re-entry indicators (want TRIGGERED to clear).
    When THESIS_PAUSED=False, signals read as exit indicators (current behavior).
    """
    triggered = sum(1 for v in signals.values() if v == 2)
    caution   = sum(1 for v in signals.values() if v == 1)

    if THESIS_PAUSED:
        # Re-entry mode: TRIGGERED signals are BAD (still blocking re-entry)
        if triggered >= 2:
            return {"n": triggered + caution, "lbl": "Triggered / 8",
                    "action": "Watching — need S3/S4/S8 to clear before re-entry", "color": "#ff6070"}
        if triggered == 1:
            return {"n": triggered + caution, "lbl": "Triggered / 8",
                    "action": "1 signal clearing — monitor for follow-through", "color": "#ffaa40"}
        if triggered == 0:
            return {"n": 0, "lbl": "Triggered / 8",
                    "action": "Signals clear — re-entry criteria met", "color": "#3dd880"}
    else:
        # Exit mode: TRIGGERED signals are GOOD (trigger exit)
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

def build_prompt(prices: dict, signals: dict, markets_str: str = "",
                 options_results: list | None = None) -> str:
    """
    Build the Claude analysis prompt from live data.
    markets_str: formatted prediction market string from kalshi.format_markets_for_prompt()
    options_results: list of active option position dicts with price/pnl (from app.py)
    """
    sig_list = "\n".join(
        f"{i+1}. {SIGNAL_NAMES[sid]}: "
        f"{'TRIGGERED' if signals[sid] == 2 else 'CAUTION' if signals[sid] == 1 else 'CLEAR'}"
        for i, sid in enumerate(SIGNAL_NAMES)
    )

    if THESIS_PAUSED:
        sig_ctx = "THESIS STATUS: PAUSED — signals read as re-entry indicators (want TRIGGERED to clear)\n" + sig_list
    else:
        sig_ctx = sig_list

    if options_results:
        opts_lines = "\n".join(
            f"- {r['opt'].get('label', r['opt']['underlying'] + ' option')}: "
            f"${r['price']:.2f}" if r.get("price") else
            f"- {r['opt'].get('label', r['opt']['underlying'] + ' option')}: N/A"
            for r in options_results
        )
        opts_section = f"ACTIVE OPTIONS:\n{opts_lines}"
    else:
        opts_section = ("OPTIONS: None currently active. "
                        "JETS puts closed Apr 8 at $0.55 (entry $1.72) — realized loss ~−$1,170.")

    wait_str = " · ".join(
        f"{w['ticker']} ({w['when'].lower()})" for w in WAITING_LIST
    )

    markets_section = f"\n{markets_str}\n" if markets_str else ""

    return f"""You are a geopolitical crisis trading analyst. Today is {date.today().strftime('%B %d, %Y')}.

THESIS STATUS: PAUSED — Ceasefire announced April 8. All positions exited.
No active thesis equity positions.
{opts_section}
Net thesis P&L: ~−$1,070 (equities +$100, options −$1,170).
Dry powder: ~$16,500 (fully available — all exits roughly break-even net).
Re-entry criteria: ceasefire breakdown or negotiations stall with 2+ signals clearing.

LEGACY HOLDS (excluded from thesis eval):
- GLD 10sh: ${prices.get('GLD', 'N/A')} (entry ${POSITIONS['GLD']['entry']}) — hold
- VTV 10sh: ${prices.get('VTV', 'N/A')} (entry ${POSITIONS['VTV']['entry']}) — hold
{markets_section}
EXIT SIGNAL STATUS:
{sig_ctx}

WAITING LIST: {wait_str}

CRITICAL DATES: Ceasefire expires {datetime.fromisoformat(DEADLINE_ISO).strftime("%b %-d")} 8pm ET

Respond with exactly 5 sections, under 70 words each:
1. SITUATION UPDATE
2. SIGNAL ASSESSMENT
3. RE-ENTRY WATCH — which signals/events would trigger thesis re-activation
4. WAITING LIST — which entries move to ready on ceasefire breakdown
5. KEY RISK before {datetime.fromisoformat(DEADLINE_ISO).strftime("%B %-d")}"""


# ── MORNING SYNC PROMPT (MERGED) ──────────────────────────────────────────────

def build_sync_prompt(prices: dict, current_signals: dict, markets_str: str,
                      options_results: list | None = None) -> str:
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
      - deadline_extension: null or ISO string "2026-05-06T20:00:00" if ceasefire is extended
      - calendar_updates: null or list of {date, event, crit} if events need adding/changing
    """
    today = date.today().strftime("%B %d, %Y")

    # Extract scenario probabilities from config
    current_a = next((s["pct"].rstrip("%") for s in SCENARIOS if "Resolution" in s["name"] and "Partial" not in s["name"]), "45")
    current_b = next((s["pct"].rstrip("%") for s in SCENARIOS if "Partial" in s["name"]), "40")
    current_c = next((s["pct"].rstrip("%") for s in SCENARIOS if "Escalation" in s["name"]), "15")

    # Extract current day number and auto-increment
    day_match = re.search(r'Day (\d+)', DAY_SUMMARY.get("label", ""))
    next_day = int(day_match.group(1)) + 1 if day_match else "N"

    if options_results:
        opts_section = "Active options:\n" + "\n".join(
            f"- {r['opt'].get('label', r['opt']['underlying'] + ' option')}: "
            + (f"${r['price']:.2f}" if r.get("price") else "N/A")
            for r in options_results
        )
    else:
        opts_section = "Options: None currently active. JETS puts closed Apr 8 at 0.55 (entry 1.72) — realized loss approximately -1170."

    sig_list = "\n".join(
        f'  "{sid}": {{"current": {current_signals[sid]}, '
        f'"name": "{SIGNAL_NAMES[sid]}", "desc": "{SIGNAL_DESC[sid]}"}}'
        for sid in SIGNAL_NAMES
    )

    thesis_status_line = "THESIS STATUS: PAUSED — signals read as re-entry indicators (want TRIGGERED to clear)" if THESIS_PAUSED else ""
    sig_ctx = thesis_status_line + ("\n" if thesis_status_line else "") + sig_list

    wait_ctx = "\n".join(
        f'  {{"ticker": "{w["ticker"]}", "current_status": "{w["status"]}", '
        f'"cond": "{w["cond"]}"}}'
        for w in WAITING_LIST
    )

    # Format prices as plain strings to avoid JSON escape issues
    def px(t): return str(round(prices[t], 2)) if t in prices else 'N/A'

    return f"""You are a geopolitical crisis trading analyst. Today is {today}.
    Produce a single JSON response combining a morning briefing AND a full intelligence brief.

    IMPORTANT: In your JSON response, do NOT use backslashes except for standard JSON escapes (\", \\, \n, \t). Do not escape dollar signs. Write dollar amounts as plain text, e.g. "$16,500" not "\\$16,500".

    THESIS STATUS: PAUSED — Ceasefire announced April 8. All positions exited.
    No active thesis equity positions.
    {opts_section}
    Net thesis P&L: approximately -1070 (equities +100, options -1170).
    Legacy holds: GLD: {px('GLD')} (entry {POSITIONS['GLD']['entry']}) | VTV: {px('VTV')} (entry {POSITIONS['VTV']['entry']})
    Dry powder: approximately 16500 (fully available — all exits roughly break-even net)
    Re-entry criteria: ceasefire breakdown or negotiations stall with 2+ signals clearing.

{markets_str}

CURRENT EXIT SIGNALS (0=clear, 1=caution, 2=triggered):
{sig_ctx}

WAITING LIST (current status):
{wait_ctx}

THESIS CONTEXT:
Operation Epic Fury (Feb 28): US/Israel struck Iran, Hormuz closed (~20% global oil).
Two-week ceasefire announced April 8. Exit rule triggered (3 signals): S3/S4/S8 all TRIGGERED.
Thesis paused — ceasefire does NOT resolve Iran's reparations demands or unconditionally reopen Hormuz.
Thesis can re-activate if ceasefire breaks down after Apr 22 expiry.
Re-entry requires ceasefire breakdown AND 2+ signals clearing again.

CURRENT SCENARIO PROBABILITIES (from last committed config):
- A (Resolution): {current_a}%
- B (Partial Resolution): {current_b}%
- C (Escalation): {current_c}%
Only adjust these if prediction market data provides specific evidence for a shift.
Maximum change per session: 5 percentage points per scenario without explicit justification.
Do not change TRIGGERED signals to lower states unless today's data contains concrete new evidence.

AI BRIEF FORMAT — for the ai_brief field, write exactly 5 sections, each under 70 words:
1. SITUATION UPDATE
2. SIGNAL ASSESSMENT
3. RE-ENTRY WATCH — which signals/events would trigger thesis re-activation
4. WAITING LIST — which entries move to ready on ceasefire breakdown
5. KEY RISK before {datetime.fromisoformat(DEADLINE_ISO).strftime("%B %-d")}

Respond ONLY with valid JSON, no preamble, no markdown fences:
{{
  "day_summary_label": "Day {next_day} - {today}",
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
  "deadline_extension": null,
  "calendar_updates": null,
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