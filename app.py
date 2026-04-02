"""
Crisis Trade Monitor v6 — Streamlit
Hormuz · Helium · False Dawn

app.py is layout orchestration only.
Edit config.py to update positions, signals, and daily summary,
OR use the Morning Sync panel to let Claude do it for you.
"""

import json
import streamlit as st
import anthropic

from config import (
    POSITIONS, JETS_PUT, SIGNAL_NAMES, SIGNAL_DESC,
    SIGNAL_DEFAULTS, WAITING_LIST, DRY_POWDER,
)
from data import fetch_prices, fetch_option_price, countdown_to_deadline
from analysis import (
    calc_pnl, calc_option_pnl, thesis_totals, legacy_totals,
    score_signals, build_prompt, build_sync_prompt, render_ai_html,
)
from components import (
    CSS, header_html, day_summary_html, scenario_bar_html,
    equity_card_html, jets_card_html, cash_card_html,
    legacy_card_html, thesis_bucket_html, legacy_bucket_html,
    wait_card_html, calendar_html, score_box_html,
)
from kalshi import fetch_kalshi_markets, fetch_polymarket_odds, format_markets_for_prompt
from github_state import (
    get_config_sha, commit_config,
    patch_day_summary, patch_signal_defaults,
)

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Crisis Trade Monitor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(CSS, unsafe_allow_html=True)

# ── SECRETS ───────────────────────────────────────────────────────────────────
# All credentials live in Streamlit secrets — never in session or UI
GITHUB_TOKEN  = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO   = st.secrets.get("GITHUB_REPO", "notagadget/crisis-monitor-dashboard")
KALSHI_KEY    = st.secrets.get("KALSHI_API_KEY", "")
ANTHROPIC_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")  # optional — falls back to UI input

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "signals" not in st.session_state:
    st.session_state.signals = dict(SIGNAL_DEFAULTS)
if "ai_output" not in st.session_state:
    st.session_state.ai_output = None
if "ai_ts" not in st.session_state:
    st.session_state.ai_ts = ""
if "api_key" not in st.session_state:
    st.session_state.api_key = ANTHROPIC_KEY
# Morning Sync state
if "sync_result" not in st.session_state:
    st.session_state.sync_result = None          # parsed JSON from Claude
if "sync_approved_signals" not in st.session_state:
    st.session_state.sync_approved_signals = {}  # {sid: bool}
if "sync_committed" not in st.session_state:
    st.session_state.sync_committed = False
if "markets_str" not in st.session_state:
    st.session_state.markets_str = ""

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

# ══════════════════════════════════════════════════════════════════════════════
# MORNING SYNC PANEL
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("⚡ Morning Sync — AI update + commit to GitHub", expanded=False):

    sync_col1, sync_col2 = st.columns([2, 1])

    with sync_col1:
        st.markdown(
            '<div style="font-family:JetBrains Mono,monospace;font-size:10px;'
            'color:#5a6880;margin-bottom:8px;">'
            'Fetches Kalshi/Polymarket odds → Claude drafts DAY_SUMMARY + suggests signal changes '
            '→ you approve → commits config.py to GitHub → Streamlit redeploys (~60s).'
            '</div>',
            unsafe_allow_html=True,
        )

        run_sync = st.button("⚡ Run Morning Sync", use_container_width=False,
                             disabled=not (ANTHROPIC_KEY or st.session_state.api_key))

    with sync_col2:
        # Show credential status
        gh_ok    = "✅" if GITHUB_TOKEN  else "❌"
        ka_ok    = "✅"
        ai_ok    = "✅" if (ANTHROPIC_KEY or st.session_state.api_key) else "❌"
        st.markdown(
            f'<div style="font-family:JetBrains Mono,monospace;font-size:10px;line-height:2;">'
            f'{gh_ok} GitHub token<br>{ka_ok} Kalshi key<br>{ai_ok} Anthropic key</div>',
            unsafe_allow_html=True,
        )

    # ── RUN SYNC ──────────────────────────────────────────────────────────────
    if run_sync:
        st.session_state.sync_result = None
        st.session_state.sync_approved_signals = {}
        st.session_state.sync_committed = False

        with st.spinner("Fetching prediction markets..."):
            kalshi_data  = fetch_kalshi_markets(KALSHI_KEY) if KALSHI_KEY else {}
            poly_data    = fetch_polymarket_odds()
            markets_str  = format_markets_for_prompt(kalshi_data, poly_data)
            st.session_state.markets_str = markets_str

        with st.spinner("Claude analyzing (~20s)..."):
            try:
                key = ANTHROPIC_KEY or st.session_state.api_key
                client = anthropic.Anthropic(api_key=key)
                msg = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1500,
                    system=(
                        "You are a geopolitical crisis trading analyst. "
                        "Respond ONLY with valid JSON as instructed. No preamble, no markdown."
                    ),
                    messages=[{
                        "role": "user",
                        "content": build_sync_prompt(
                            prices, option_price,
                            st.session_state.signals,
                            markets_str,
                        ),
                    }],
                )
                raw = msg.content[0].text.strip()
                # Strip accidental markdown fences
                raw = raw.replace("```json", "").replace("```", "").strip()
                st.session_state.sync_result = json.loads(raw)
                # Pre-approve all signal suggestions by default
                sr = st.session_state.sync_result
                st.session_state.sync_approved_signals = {
                    sid: True for sid in sr.get("signal_suggestions", {})
                }
            except json.JSONDecodeError as e:
                st.error(f"Claude returned malformed JSON: {e}\n\nRaw: {raw[:300]}")
            except Exception as e:
                st.error(f"Sync error: {e}")

    # ── REVIEW UI ─────────────────────────────────────────────────────────────
    sr = st.session_state.sync_result
    if sr and not st.session_state.sync_committed:

        st.divider()

        # Key insight callout
        if sr.get("key_insight"):
            st.markdown(
                f'<div style="background:#fff7e8;border-left:4px solid #d48818;'
                f'padding:10px 14px;border-radius:4px;font-size:12px;font-weight:600;'
                f'color:#b86800;">⚡ {sr["key_insight"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)

        # DAY SUMMARY — auto-committed, just show preview
        st.markdown("**📋 Day Summary** *(auto-committed)*")
        st.markdown(
            f'<div style="background:#f4f6f9;border:1px solid #d0d5e0;border-radius:4px;'
            f'padding:10px 14px;font-size:11px;color:#2a3848;line-height:1.6;">'
            f'<b>{sr.get("day_summary_label", "")}</b><br>'
            f'{sr.get("day_summary_body", "")}'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        # SIGNAL SUGGESTIONS — approval required per signal
        sig_sugg = sr.get("signal_suggestions", {})
        if sig_sugg:
            st.markdown("**🚦 Signal Suggestions** *(check to approve each)*")
            state_labels = {0: "CLEAR 🔵", 1: "CAUTION 🟡", 2: "TRIGGERED 🔴"}
            changed_signals = {
                sid: d for sid, d in sig_sugg.items()
                if d.get("suggested") != st.session_state.signals.get(sid)
            }
            if not changed_signals:
                st.caption("No signal changes suggested.")
            else:
                for sid, d in changed_signals.items():
                    current  = st.session_state.signals.get(sid, 0)
                    suggested = d.get("suggested", current)
                    reason   = d.get("reason", "")
                    approved = st.session_state.sync_approved_signals.get(sid, True)
                    col_a, col_b = st.columns([1, 8])
                    with col_a:
                        checked = st.checkbox("", value=approved, key=f"approve_{sid}")
                        st.session_state.sync_approved_signals[sid] = checked
                    with col_b:
                        st.markdown(
                            f'<div style="font-family:JetBrains Mono,monospace;font-size:10px;'
                            f'padding:6px 0;">'
                            f'<b>{SIGNAL_NAMES[sid]}</b>: '
                            f'{state_labels[current]} → {state_labels[suggested]}<br>'
                            f'<span style="color:#5a6880;">{reason}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
            st.markdown("<br>", unsafe_allow_html=True)

        # WAITING LIST SUGGESTIONS — informational only (manual edit still required)
        wl_sugg = sr.get("waiting_list_suggestions", [])
        if wl_sugg:
            st.markdown("**📋 Waiting List Notes** *(informational — edit config.py to change)*")
            for w in wl_sugg:
                st.markdown(
                    f'<div style="font-family:JetBrains Mono,monospace;font-size:10px;'
                    f'color:#2a3848;padding:4px 0;">'
                    f'<b>{w.get("ticker")}</b> → {w.get("suggested_status","?").upper()} · '
                    f'<span style="color:#5a6880;">{w.get("reason","")}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("<br>", unsafe_allow_html=True)

        # PREDICTION MARKETS RAW
        if st.session_state.markets_str:
            with st.expander("📊 Raw prediction market data used"):
                st.code(st.session_state.markets_str)

        # COMMIT BUTTON
        if not GITHUB_TOKEN:
            st.warning("GITHUB_TOKEN not set in Streamlit secrets — cannot commit.")
        else:
            commit_clicked = st.button(
                "✅ Commit to GitHub → Redeploy",
                type="primary",
                use_container_width=False,
            )
            if commit_clicked:
                with st.spinner("Reading current config.py from GitHub..."):
                    try:
                        config_text, sha = get_config_sha(GITHUB_REPO, GITHUB_TOKEN)

                        # Always auto-apply DAY_SUMMARY
                        config_text = patch_day_summary(
                            config_text,
                            sr.get("day_summary_label", ""),
                            sr.get("day_summary_body", ""),
                        )

                        # Apply only approved signal changes
                        new_signals = dict(st.session_state.signals)
                        for sid, d in sig_sugg.items():
                            if st.session_state.sync_approved_signals.get(sid):
                                new_signals[sid] = d.get("suggested", new_signals[sid])
                        config_text = patch_signal_defaults(config_text, new_signals)

                        commit_config(GITHUB_REPO, GITHUB_TOKEN, config_text, sha)
                        st.session_state.sync_committed = True
                        # Update live session signals immediately
                        st.session_state.signals = new_signals
                        st.rerun()
                    except Exception as e:
                        st.error(f"Commit failed: {e}")

    elif st.session_state.sync_committed:
        st.success("✅ Committed to GitHub. Streamlit is redeploying (~60s). Refresh to see updated config.")

# ── AI BRIEF + EXIT SIGNALS ───────────────────────────────────────────────────
col_ai, col_sig = st.columns([3, 1])

with col_ai:
    st.markdown('<div class="sec-label">AI Intelligence Brief</div>', unsafe_allow_html=True)
    key_col, btn_col = st.columns([4, 1])
    with key_col:
        # Only show API key input if not set in secrets
        if not ANTHROPIC_KEY:
            api_key = st.text_input(
                "API Key", value=st.session_state.api_key,
                type="password", placeholder="sk-ant-...", label_visibility="collapsed",
            )
            st.session_state.api_key = api_key
        else:
            api_key = ANTHROPIC_KEY
    with btn_col:
        run_clicked = st.button("⚡ Run AI Analysis", use_container_width=True)

    if run_clicked:
        effective_key = ANTHROPIC_KEY or st.session_state.api_key
        if not effective_key.startswith("sk-ant"):
            st.error("Enter a valid Anthropic API key (sk-ant-...)")
        else:
            with st.spinner("Analyzing (~15s)..."):
                try:
                    client = anthropic.Anthropic(api_key=effective_key)
                    msg = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1000,
                        system="Concise geopolitical crisis trading analyst. Plain text. Direct. Specific tickers and prices.",
                        messages=[{
                            "role": "user",
                            "content": build_prompt(
                                prices, option_price,
                                st.session_state.signals,
                                st.session_state.markets_str,
                            ),
                        }],
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

for i, ticker in enumerate(thesis_tickers[:4]):
    price = prices.get(ticker, POSITIONS[ticker]["entry"])
    pnl   = calc_pnl(ticker, price)
    with pcols[i]:
        st.markdown(equity_card_html(ticker, price, pnl), unsafe_allow_html=True)

with pcols[4]:
    jets_price = prices.get("JETS", JETS_PUT.get("stop_underlying", 25.0))
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
    'text-align:right;padding:6px 20px;">Credentials in Streamlit secrets · never persisted in session</div>',
    unsafe_allow_html=True,
)
