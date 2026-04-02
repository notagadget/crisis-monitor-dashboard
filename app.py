"""
Crisis Trade Monitor v6 — Streamlit
Hormuz · Helium · False Dawn

app.py is layout orchestration only.
Edit config.py to update positions, signals, and daily summary.
"""

import streamlit as st
import anthropic

from config import POSITIONS, SIGNAL_NAMES, SIGNAL_DESC, SIGNAL_DEFAULTS, WAITING_LIST
from data import fetch_prices, fetch_option_price, countdown_to_deadline
from analysis import (
    calc_pnl, calc_option_pnl, thesis_totals, legacy_totals,
    score_signals, build_prompt, render_ai_html,
)
from components import (
    CSS, header_html, day_summary_html, scenario_bar_html,
    equity_card_html, jets_card_html, cash_card_html,
    legacy_card_html, thesis_bucket_html, legacy_bucket_html,
    wait_card_html, calendar_html, score_box_html,
)

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Crisis Trade Monitor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(CSS, unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "signals" not in st.session_state:
    st.session_state.signals = dict(SIGNAL_DEFAULTS)
if "ai_output" not in st.session_state:
    st.session_state.ai_output = None
if "ai_ts" not in st.session_state:
    st.session_state.ai_ts = ""
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# ── LIVE DATA (fetched once per page load) ────────────────────────────────────
prices       = fetch_prices()
option_price = fetch_option_price()
opt_pnl, opt_pct = calc_option_pnl(option_price)
thesis       = thesis_totals(prices, opt_pnl)
legacy       = legacy_totals(prices)
score        = score_signals(st.session_state.signals)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(header_html(), unsafe_allow_html=True)
st.markdown(day_summary_html(), unsafe_allow_html=True)
st.markdown(scenario_bar_html(countdown_to_deadline()), unsafe_allow_html=True)

# ── AI BRIEF + EXIT SIGNALS ───────────────────────────────────────────────────
col_ai, col_sig = st.columns([3, 1])

with col_ai:
    st.markdown('<div class="sec-label">AI Intelligence Brief</div>', unsafe_allow_html=True)
    key_col, btn_col = st.columns([4, 1])
    with key_col:
        api_key = st.text_input(
            "API Key", value=st.session_state.api_key,
            type="password", placeholder="sk-ant-...", label_visibility="collapsed",
        )
        st.session_state.api_key = api_key
    with btn_col:
        run_clicked = st.button("⚡ Run AI Analysis", use_container_width=True)

    if run_clicked:
        if not api_key.startswith("sk-ant"):
            st.error("Enter a valid Anthropic API key (sk-ant-...)")
        else:
            with st.spinner("Analyzing (~15s)..."):
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    msg = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1000,
                        system="Concise geopolitical crisis trading analyst. Plain text. Direct. Specific tickers and prices.",
                        messages=[{"role": "user", "content": build_prompt(prices, option_price, st.session_state.signals)}],
                    )
                    st.session_state.ai_output = msg.content[0].text
                    st.session_state.ai_ts = __import__("datetime").datetime.now().strftime("%H:%M:%S")
                except Exception as e:
                    st.error(f"API Error: {e}")

    if st.session_state.ai_output:
        st.markdown(
            f'<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#5a6880;margin-bottom:4px;">'
            f'Updated {st.session_state.ai_ts}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="ai-box">{render_ai_html(st.session_state.ai_output)}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="ai-box" style="text-align:center;padding:30px 20px;">'
            '<span style="font-family:IBM Plex Sans,sans-serif;font-size:12px;color:#5a6880;line-height:1.7;">'
            'Enter your Anthropic API key and click <b>Run AI Analysis</b>.<br><br>'
            'Claude will assess the situation, score exit signals, flag position risks,<br>'
            'and identify waiting list entries ready to enter. (~15 seconds)'
            '</span></div>',
            unsafe_allow_html=True,
        )

with col_sig:
    st.markdown('<div class="sec-label">Exit Signals</div>', unsafe_allow_html=True)
    st.caption("Click to cycle: Clear → Caution → Triggered")
    emoji = {0: "🔵", 1: "🟡", 2: "🔴"}
    for sid in SIGNAL_NAMES:
        state = st.session_state.signals[sid]
        if st.button(f"{emoji[state]} {SIGNAL_NAMES[sid]}", key=f"sig_{sid}",
                     use_container_width=True, help=SIGNAL_DESC[sid]):
            st.session_state.signals[sid] = (state + 1) % 3
            st.rerun()
    st.markdown(score_box_html(score), unsafe_allow_html=True)

# ── POSITIONS ─────────────────────────────────────────────────────────────────
st.markdown('<br>', unsafe_allow_html=True)
thesis_tickers = [t for t, p in POSITIONS.items() if p["thesis"]]
pcols = st.columns(6)

for i, ticker in enumerate(thesis_tickers):
    price = prices.get(ticker, POSITIONS[ticker]["entry"])
    pnl   = calc_pnl(ticker, price)
    with pcols[i]:
        st.markdown(equity_card_html(ticker, price, pnl), unsafe_allow_html=True)

with pcols[4]:
    jets_price = prices.get("JETS")
    st.markdown(jets_card_html(jets_price, option_price, opt_pnl, opt_pct), unsafe_allow_html=True)

with pcols[5]:
    st.markdown(cash_card_html(), unsafe_allow_html=True)

# Legacy holds
st.markdown(
    '<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#5a6880;'
    'letter-spacing:1px;text-transform:uppercase;margin:12px 0 6px;'
    'padding-top:8px;border-top:1px dashed #d0d5e0;">'
    'Legacy Holds — excluded from thesis P&L</div>',
    unsafe_allow_html=True,
)
lc1, lc2, _ = st.columns([1, 1, 4])
for col, ticker in [(lc1, "GLD"), (lc2, "VTV")]:
    price = prices.get(ticker, POSITIONS[ticker]["entry"])
    pnl   = calc_pnl(ticker, price)
    with col:
        st.markdown(legacy_card_html(ticker, price, pnl), unsafe_allow_html=True)

# P&L buckets
buck1, buck2 = st.columns(2)
with buck1:
    st.markdown(thesis_bucket_html(thesis["equity_rows"], thesis["jets_pnl"], thesis["total"]), unsafe_allow_html=True)
with buck2:
    st.markdown(legacy_bucket_html(legacy["rows"], legacy["total"]), unsafe_allow_html=True)

# ── WAITING LIST ──────────────────────────────────────────────────────────────
st.markdown('<br><div class="sec-label">Waiting List</div>', unsafe_allow_html=True)
wcols = st.columns(len(WAITING_LIST))
for i, w in enumerate(WAITING_LIST):
    with wcols[i]:
        st.markdown(wait_card_html(w), unsafe_allow_html=True)

# ── CALENDAR + FOOTER ─────────────────────────────────────────────────────────
st.markdown(calendar_html(), unsafe_allow_html=True)
st.markdown(
    '<div style="font-family:JetBrains Mono,monospace;font-size:8px;color:#5a6880;'
    'text-align:right;padding:6px 20px;">API key stored in session only · never persisted</div>',
    unsafe_allow_html=True,
)

# ── IMPORT GUARD (needed for jets_card_html __import__ reference) ─────────────
from config import JETS_PUT
