"""
components.py — HTML/CSS builders for each dashboard section.
Each function returns a string passed to st.markdown(..., unsafe_allow_html=True).
No data fetching or business logic here.
"""

from config import (
    APP_VERSION, SCENARIOS, WAITING_LIST, CALENDAR, DAY_SUMMARY, DRY_POWDER, POSITIONS,
    LAST_UPDATED,
)


# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

:root {
  --bg:#eef0f5; --surface:#fff; --surface2:#f4f6f9; --border:#d0d5e0;
  --text:#0e1520; --text2:#2a3848; --text3:#5a6880;
  --acc:#b86800; --acc-bg:#fff7e8; --acc-border:#d48818;
  --red:#a81828; --red-bg:#fff0f2; --red-border:#d83040;
  --grn:#126030; --grn-bg:#ebf7f0; --grn-border:#24a060;
  --blu:#0b4580; --blu-bg:#edf3fc; --blu-border:#2c68c0;
  --pur:#4420a0; --pur-bg:#f0eeff; --pur-border:#6848c8;
}
#MainMenu,footer,header{visibility:hidden}
.stApp{background:var(--bg);font-family:'IBM Plex Sans',sans-serif}
.block-container{padding:0!important;max-width:100%!important}

.hdr{background:#0e1520;padding:12px 24px;display:flex;align-items:center;justify-content:space-between}
.brand{font-size:14px;font-weight:700;color:#fff;letter-spacing:.5px;margin:0}
.brand-sub{font-family:'JetBrains Mono',monospace;font-size:10px;color:rgba(255,255,255,0.4)}
.pill-live{font-family:'JetBrains Mono',monospace;font-size:10px;padding:3px 10px;
  border:1px solid #24a060;color:#3dd880;background:rgba(36,160,96,0.12);
  border-radius:20px;display:inline-flex;align-items:center;gap:5px}
.pdot{width:6px;height:6px;border-radius:50%;background:#3dd880;
  display:inline-block;animation:blink 2s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}

.sec-label{font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--text3);
  letter-spacing:1.5px;text-transform:uppercase;padding-bottom:6px;
  border-bottom:1px solid var(--border);margin-bottom:10px}

.pos-card{background:var(--surface);border:1.5px solid var(--border);
  border-radius:6px;padding:10px 12px;margin-bottom:8px}
.pos-card.warn{border-color:var(--acc-border);background:var(--acc-bg)}
.pos-card.opts{border-left:4px solid var(--pur)}
.pos-card.hold{background:var(--surface2);opacity:.8}
.pos-ticker{font-size:15px;font-weight:700;color:var(--text);margin:0}
.pos-type{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--text3);
  letter-spacing:.5px;text-transform:uppercase;margin-bottom:4px}
.pos-entry{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text3)}
.pos-price{font-size:16px;font-weight:700;color:var(--text)}
.stop-badge{font-family:'JetBrains Mono',monospace;font-size:9px;padding:2px 7px;
  border:1px solid var(--red-border);color:var(--red);border-radius:3px;
  background:var(--red-bg);display:inline-block;margin-top:4px}
.stop-badge.watch{border-color:var(--acc-border);color:var(--acc);background:var(--acc-bg)}
.stop-badge.hold{border-color:var(--border);color:var(--text3);background:var(--surface2)}

.score-box{background:#0e1520;border-radius:6px;padding:12px 14px;
  display:flex;align-items:center;gap:14px;margin-top:10px}
.score-num{font-size:28px;font-weight:700;color:#fff}
.score-lbl{font-family:'JetBrains Mono',monospace;font-size:9px;
  color:rgba(255,255,255,0.45);letter-spacing:.5px}
.score-act{font-size:11px;font-weight:600}

.sc-bar{display:flex;gap:0;border:1px solid var(--border);border-radius:6px;
  overflow:hidden;margin-bottom:12px}
.sc-item{flex:1;padding:10px 14px;border-right:1px solid var(--border)}
.sc-item:last-child{border-right:none}
.sc-item.active{background:var(--acc-bg)}
.sc-pct{font-size:22px;font-weight:700}
.sc-name{font-size:12px;font-weight:600}
.sc-desc{font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--text3);margin-top:2px}

.bucket-thesis{background:#0e1520;border-radius:6px;padding:14px;color:#fff}
.bucket-legacy{background:var(--surface);border:1.5px solid var(--border);border-radius:6px;padding:14px}
.bucket-row{display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;
  font-size:10px;margin-bottom:3px}
.bucket-total{display:flex;justify-content:space-between;font-size:14px;font-weight:700;
  margin-top:10px;padding-top:10px}

.wc{border:1.5px solid var(--border);border-radius:6px;padding:10px 12px;
  background:var(--surface);margin-bottom:8px}
.wc.ready{border-color:var(--grn-border);background:var(--grn-bg);border-top:3px solid var(--grn-border)}
.wc.event{border-top:3px solid var(--blu)}
.wc.watching{border-top:3px solid var(--acc-border);background:var(--acc-bg)}
.wc.patience{border-top:3px solid var(--border)}
.wc-ticker{font-weight:700;font-size:13px}
.wc-when{font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.5px;
  text-transform:uppercase;margin-bottom:4px}
.wc.ready .wc-when{color:var(--grn)}
.wc.event .wc-when{color:var(--blu)}
.wc.watching .wc-when{color:var(--acc)}
.wc.patience .wc-when{color:var(--text3)}
.wc-alloc{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;
  color:var(--acc);margin-top:6px}
.wc.ready .wc-alloc{color:var(--grn)}

.cal-strip{background:var(--surface);border-top:1px solid var(--border);
  padding:8px 20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.cal-lbl{font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--text3);
  letter-spacing:.5px;text-transform:uppercase}

.ai-box{background:var(--surface2);border:1.5px solid var(--border);border-radius:6px;
  padding:14px;font-family:'JetBrains Mono',monospace;font-size:11px;
  line-height:1.8;color:var(--text2);min-height:180px}
.tag-d{display:inline-block;font-size:9px;padding:1px 6px;border-radius:3px;
  background:var(--red-bg);color:var(--red);border:1px solid var(--red-border);
  font-family:'JetBrains Mono',monospace}
.tag-w{display:inline-block;font-size:9px;padding:1px 6px;border-radius:3px;
  background:var(--acc-bg);color:var(--acc);border:1px solid var(--acc-border);
  font-family:'JetBrains Mono',monospace}
.tag-g{display:inline-block;font-size:9px;padding:1px 6px;border-radius:3px;
  background:var(--grn-bg);color:var(--grn);border:1px solid var(--grn-border);
  font-family:'JetBrains Mono',monospace}
</style>
"""


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _pnl_style(pnl: float) -> tuple[str, str]:
    """Returns (background_color, text_color) for a P&L value."""
    if pnl > 0:  return "#ebf7f0", "#126030"
    if pnl < 0:  return "#fff0f2", "#a81828"
    return "#f4f6f9", "#5a6880"

def _sign(val: float) -> str:
    return "+" if val >= 0 else ""


# ── SECTION BUILDERS ──────────────────────────────────────────────────────────

def header_html() -> str:
    return f"""
<div class="hdr">
  <div>
    <div class="brand">CRISIS TRADE MONITOR {APP_VERSION}</div>
    <div class="brand-sub">Hormuz · Helium · False Dawn &nbsp;|&nbsp; {LAST_UPDATED}</div>
  </div>
  <div style="display:flex;gap:10px;align-items:center;">
    <span class="pill-live"><span class="pdot"></span>Live</span>
  </div>
</div>"""


def day_summary_html() -> str:
    s = DAY_SUMMARY
    return (
        f'<div style="background:#fff7e8;border-left:4px solid #d48818;padding:12px 20px;margin-bottom:4px;">'
        f'<div style="font-size:11px;font-weight:700;color:#b86800;text-transform:uppercase;'
        f'letter-spacing:.3px;margin-bottom:5px;">{s["label"]}</div>'
        f'<div style="font-size:12px;color:#2a3848;line-height:1.65;">{s["body"]}</div>'
        f'</div>'
    )


def scenario_bar_html(countdown: str) -> str:
    items = ""
    for sc in SCENARIOS:
        cls = " active" if sc["active"] else ""
        items += (
            f'<div class="sc-item{cls}">'
            f'<div class="sc-pct" style="color:{sc["color"]};">{sc["pct"]}</div>'
            f'<div class="sc-name">{sc["name"]}</div>'
            f'<div class="sc-desc">{sc["desc"]}</div>'
            f'</div>'
        )
    items += (
        f'<div class="sc-item" style="text-align:right;">'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#5a6880;'
        f'letter-spacing:.5px;text-transform:uppercase;">Apr 22 Ceasefire</div>'
        f'<div style="font-size:20px;font-weight:700;color:#a81828;">{countdown}</div>'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#5a6880;">Ceasefire expires · 8pm ET</div>'
        f'</div>'
    )
    return f'<div class="sc-bar">{items}</div>'


def equity_card_html(ticker: str, price: float, pnl: float) -> str:
    p = POSITIONS[ticker]
    cost = p["entry"] * p["shares"]
    pct = (pnl / cost) * 100
    bg, fg = _pnl_style(pnl)
    return (
        f'<div class="pos-card">'
        f'<div class="pos-ticker">{ticker}</div>'
        f'<div class="pos-type">Equity · {p["shares"]} shares</div>'
        f'<div class="pos-entry">Entry ${p["entry"]:.2f} · Basis ${cost:,.0f}</div>'
        f'<div class="pos-price">${price:.2f}</div>'
        f'<div style="margin-top:4px;font-family:JetBrains Mono,monospace;font-size:11px;'
        f'padding:2px 8px;border-radius:3px;display:inline-block;background:{bg};color:{fg};">'
        f'{_sign(pnl)}${pnl:,.2f} &nbsp;{_sign(pct)}{pct:.1f}%</div><br>'
        f'<span class="stop-badge">Stop ${p["stop"]:.2f}</span>' if p["stop"] is not None else ''
        f'</div>'
    )


def option_card_html(opt: dict, underlying: float, option_price: float | None,
                     pnl: float | None, pct: float | None,
                     option_source: str | None = None) -> str:
    """Generic option position card. opt is a dict from OPTIONS_POSITIONS."""
    source_tag = f" ({option_source})" if option_source and option_source != "last" else ""
    opt_str  = f"${option_price:.2f}{source_tag}" if option_price else "N/A"
    pnl_str  = f"{_sign(pnl or 0)}${(pnl or 0):,.2f}" if pnl is not None else "N/A"
    pct_str  = f"{_sign(pct or 0)}{(pct or 0):.1f}%" if pct is not None else ""
    bg, fg   = _pnl_style(pnl or -1)
    from datetime import date as _date
    _exp = _date(*[int(x) for x in opt["expiry_date"].split("-")])
    days_left = (_exp - _date.today()).days
    label = opt.get("label", f"{opt['underlying']} {opt.get('option_type', 'option')}s")
    stop_html = (
        f'<span class="stop-badge watch" style="margin-top:6px;">'
        f'Stop: {opt["underlying"]} above ${opt["stop_underlying"]}</span>'
        if opt.get("stop_underlying") else ""
    )
    return (
        f'<div class="pos-card opts">'
        f'<div class="pos-ticker">{label}</div>'
        f'<div class="pos-type">{opt["contracts"]}× ${opt["strike"]} '
        f'{opt["expiry_label"]} · {days_left}d</div>'
        f'<div class="pos-entry">Paid ${opt["premium_paid"]:.2f} · now {opt_str}</div>'
        f'<div class="pos-price">${underlying:.2f} '
        f'<span style="font-size:10px;color:#5a6880;">underlying</span></div>'
        f'<div style="margin-top:4px;font-family:JetBrains Mono,monospace;font-size:11px;'
        f'padding:2px 8px;border-radius:3px;display:inline-block;background:{bg};color:{fg};">'
        f'{pnl_str} &nbsp;{pct_str}</div><br>'
        f'{stop_html}'
        f'</div>'
    )


def cash_card_html() -> str:
    wait_ready = [w["ticker"] for w in WAITING_LIST if w["status"] in ("ready", "event")]
    lines = "<br>".join(wait_ready[:4])
    return (
        f'<div class="pos-card" style="border:1.5px dashed #d0d5e0;background:#f4f6f9;">'
        f'<div class="pos-ticker" style="color:#5a6880;">Cash</div>'
        f'<div class="pos-type">Dry Powder</div>'
        f'<div style="font-size:18px;font-weight:700;color:#0b4580;margin-top:6px;">'
        f'~${DRY_POWDER:,}</div>'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:9px;'
        f'color:#5a6880;margin-top:8px;line-height:1.7;">{lines}</div>'
        f'</div>'
    )


def legacy_card_html(ticker: str, price: float, pnl: float) -> str:
    p = POSITIONS[ticker]
    cost = p["entry"] * p["shares"]
    pct = (pnl / cost) * 100
    bg, fg = _pnl_style(pnl)
    return (
        f'<div class="pos-card hold">'
        f'<div class="pos-ticker">{ticker}</div>'
        f'<div class="pos-type">Hold · {p["shares"]} shares</div>'
        f'<div class="pos-entry">Entry ${p["entry"]:.2f} · Basis ${cost:,.0f}</div>'
        f'<div class="pos-price">${price:.2f}</div>'
        f'<div style="margin-top:4px;font-family:JetBrains Mono,monospace;font-size:11px;'
        f'padding:2px 8px;border-radius:3px;display:inline-block;background:{bg};color:{fg};">'
        f'{_sign(pnl)}${pnl:,.0f} &nbsp;{_sign(pct)}{pct:.1f}%</div><br>'
        f'<span class="stop-badge hold">Hold · not thesis capital</span>'
        f'</div>'
    )


def thesis_bucket_html(equity_rows: dict, options_rows: list, total: float) -> str:
    """
    equity_rows: {ticker: pnl}
    options_rows: [{"label": str, "pnl": float|None}, ...]
    """
    eq_html = "".join(
        f'<div class="bucket-row"><span>{t} {POSITIONS[t]["shares"]}sh</span>'
        f'<span style="color:{"#3dd880" if v>=0 else "#ff6070"};">'
        f'{_sign(v)}${v:,.2f}</span></div>'
        for t, v in equity_rows.items()
    )
    opts_html = "".join(
        f'<div class="bucket-row"><span>{r["label"]}</span>'
        f'<span style="color:{"#3dd880" if (r["pnl"] or 0)>=0 else "#ff6070"};">'
        f'{_sign(r["pnl"] or 0)}${(r["pnl"] or 0):,.2f}</span></div>'
        for r in options_rows
    )
    total_color = "#ff6070" if total < 0 else "#3dd880"
    return (
        f'<div class="bucket-thesis">'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:9px;letter-spacing:1px;'
        f'text-transform:uppercase;color:rgba(255,255,255,0.45);margin-bottom:8px;">Thesis P&L — Active Trade</div>'
        f'{eq_html}'
        f'{opts_html}'
        f'<div class="bucket-total" style="border-top:1px solid rgba(255,255,255,0.12);color:#fff;">'
        f'<span>Thesis Total</span><span style="color:{total_color};">{_sign(total)}${total:,.0f}</span></div>'
        f'<div style="font-family:IBM Plex Sans,sans-serif;font-size:10px;color:rgba(255,255,255,0.5);'
        f'margin-top:6px;line-height:1.5;">Thesis paused. All positions exited Apr 8. Re-entry on ceasefire breakdown.</div>'
        f'</div>'
    )


def legacy_bucket_html(rows: dict, total: float) -> str:
    rows_html = "".join(
        f'<div class="bucket-row"><span>{t} {POSITIONS[t]["shares"]}sh</span>'
        f'<span style="color:{"#126030" if v >= 0 else "#a81828"};">{_sign(v)}${v:,.0f}</span></div>'
        for t, v in rows.items()
    )
    total_color = "#126030" if total >= 0 else "#a81828"
    return (
        f'<div class="bucket-legacy">'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:9px;letter-spacing:1px;'
        f'text-transform:uppercase;color:#5a6880;margin-bottom:8px;">Legacy P&L — Pre-existing Holds</div>'
        f'{rows_html}'
        f'<div class="bucket-total" style="border-top:1px solid #d0d5e0;color:#0e1520;">'
        f'<span>Legacy Total</span><span style="color:{total_color};">{_sign(total)}${total:,.0f}</span></div>'
        f'<div style="font-family:IBM Plex Sans,sans-serif;font-size:10px;color:#5a6880;'
        f'margin-top:6px;line-height:1.5;">'
        f'Independent of the Hormuz thesis. Do not use to offset thesis losses.</div>'
        f'</div>'
    )


def wait_card_html(w: dict) -> str:
    return (
        f'<div class="wc {w["status"]}">'
        f'<div class="wc-ticker">{w["ticker"]}</div>'
        f'<div class="wc-when">{w["when"]}</div>'
        f'<div style="font-size:10px;color:#2a3848;line-height:1.4;">{w["cond"]}</div>'
        f'<div class="wc-alloc">{w["alloc"]}</div>'
        f'</div>'
    )


def calendar_html() -> str:
    items = ""
    for ev in CALENDAR:
        color = "#a81828" if ev["crit"] else "#5a6880"
        items += (
            f'<span style="font-family:JetBrains Mono,monospace;font-size:10px;">'
            f'<span style="font-weight:600;color:{color};">{ev["date"]}</span> '
            f'<span style="color:#5a6880;">{ev["event"]}</span></span> &nbsp;'
        )
    return (
        f'<div class="cal-strip">'
        f'<span class="cal-lbl">Key Dates</span>'
        f'{items}'
        f'</div>'
    )


def prediction_markets_html(kalshi: list, poly: list) -> str:
    """Horizontal strip showing live prediction market odds."""
    all_markets = [m for m in kalshi + poly if not m.get("error")]
    items = []

    if not all_markets:
        items.append(
            '<div style="flex:1;min-width:0;">'
            '<div style="color:var(--text3);font-size:10px;">Markets unavailable</div></div>'
        )
    else:
        for m in all_markets[:8]:
            source = m.get("source", "").upper()
            src_label = "K" if source == "KALSHI" else "PM"
            title = m.get("title", "")
            short_title = (title[:45] + "...") if len(title) > 48 else title
            pct = m.get("yes_pct", "?")
            items.append(
                f'<div style="flex:1;min-width:100px;max-width:180px;">'
                f'<div style="font-size:7px;letter-spacing:.3px;'
                f'color:var(--text3);margin-bottom:3px;overflow:hidden;'
                f'text-overflow:ellipsis;white-space:nowrap;" title="{title}">'
                f'<span style="background:var(--border);border-radius:2px;padding:0 3px;'
                f'margin-right:3px;font-size:7px;">{src_label}</span>'
                f'{short_title}</div>'
                f'<span style="font-size:16px;font-weight:700;color:var(--text);">'
                f'{pct}%</span>'
                f'<span style="color:var(--text3);font-size:9px;"> YES</span>'
                f'</div>'
            )

    return (
        f'<div style="background:var(--surface);border:1px solid var(--border);border-radius:4px;'
        f'padding:8px 20px;margin-bottom:8px;display:flex;gap:24px;align-items:flex-start;'
        f'font-family:JetBrains Mono,monospace;font-size:10px;">'
        f'<span style="font-size:8px;letter-spacing:1px;text-transform:uppercase;'
        f'color:var(--text3);align-self:center;white-space:nowrap;">MARKETS</span>'
        + "".join(items)
        + "</div>"
    )


def score_box_html(score: dict) -> str:
    return (
        f'<div class="score-box">'
        f'<div class="score-num">{score["n"]}</div>'
        f'<div>'
        f'<div class="score-lbl">{score["lbl"]}</div>'
        f'<div class="score-act" style="color:{score["color"]};">{score["action"]}</div>'
        f'</div></div>'
    )
