# Crisis Trade Monitor — Project Context
Last updated: April 9, 2026 (Day 40 — Thesis Paused / Ceasefire Day 2)

## Changelog
- Apr 9: Day 40. Ceasefire holding but Hormuz effectively closed (5–9 ships/24hrs vs 100+ norm).
  Iran halted tanker traffic citing Lebanon strikes; released mine-routing map. IRGC and US have
  incompatible public accounts of the deal. Islamabad talks Sat Apr 12 (Vance/Witkoff/Kushner).
  Scenarios updated: B now modal (45%), A reduced to 40%. S3/S4/S8 remain TRIGGERED.
- Apr 8: All thesis positions exited. Ceasefire announced. Signals updated. v0.92.
  - JETS puts closed $0.55 (entry $1.72) → −$1,170
  - RTX/NOC/LIN/VTIP equities: ~+$100 combined
  - Net thesis P&L: ~−$1,070
- Apr 5: v0.7. S3 TRIGGERED. Deadline extended to Apr 8. F-15E downed.

## The Thesis
Operation Epic Fury (Feb 28, 2026): US/Israel struck Iran, killing Khamenei.
Iran closed Strait of Hormuz (~20% global oil). Downstream: helium/LNG (Qatar
Ras Laffan force majeure), fertilizer (urea/sulfur).

**Current phase: Thesis Paused — Ceasefire Day 1 (Day 39). Extremely fragile.**
Two-week ceasefire declared April 7/8. Thesis positions fully exited.

### Ceasefire Terms (key facts)
- US/Israel halt attacks on Iran for 2 weeks (expires April 22)
- Iran agrees to allow "safe passage" through Hormuz "via coordination with IRGC"
- Iran's 10-point proposal accepted as "workable basis for negotiations"
- Islamabad talks: Vance + Witkoff + Kushner, April 12 (Saturday)
- **Already under strain:** Iran IRGC halted tanker traffic citing Israeli strikes in Lebanon
- Iran parliamentary speaker claims 3 clauses already violated
- Only 2 ships transited Hormuz on Day 1 vs. pre-war ~100-130/day
- Israel explicitly excluded Lebanon from ceasefire scope
- Trump: Hormuz must open "without limitation, including tolls"
- Iran reportedly seeking crypto toll payments — directly at odds with US position

### Ceasefire is NOT resolution:
- Iran's reparations demands unresolved
- Enriched uranium removal demanded by US/Israel vs. Iranian sovereignty
- Lebanon fight ongoing (Israel-Hezbollah unconstrained)
- Hormuz "coordinated passage" ≠ unconditional reopening

## Realized P&L
- JETS puts (10× $23 Jun18): entered $1.72, exited $0.55 → −$1,170
- RTX/NOC/LIN/VTIP equities: ~+$100 combined
- **Net thesis P&L: ~−$1,070**
- Thesis active: Mar 30 – Apr 8, 2026 (9 days)

## Active Positions
None. Thesis paused.

## Legacy Holds
| Ticker | Shares | Thesis-Start Price (Mar 30) | Notes |
|--------|--------|----------------------------|-------|
| GLD    | 10     | $414.57                    | Hold  |
| VTV    | 10     | $194.16                    | Hold  |
| RKLB   | 200    | $61.68 basis               | May $70 CCs written; in green. No further concentration. |

## Re-Entry Criteria
Primary trigger: Ceasefire breaks down after Apr 22 expiry OR Islamabad talks collapse
Secondary: Iran halts Hormuz traffic for 48h+ (IRGC already halted once Day 1)
Signal requirement: S3 AND S8 must downgrade (clear) before re-entering energy longs
Note: S4 clears if Iran pragmatist faction loses influence or hardliners take over
Waiting list priority unchanged — XOM/CVX first, then APD, MOS/CF

## Waiting List (all patience — ceasefire pause)
1. XOM/CVX — $3,000 — Post-ceasefire breakdown or Islamabad talks failure
2. APD — $2,000 — Watching (Ras Laffan still structurally closed; ceasefire irrelevant)
3. MOS/CF — $2,000 — Watching (fertilizer disruption persists structurally)
4. USO calls — $1,000–1,500 — Post-ceasefire breakdown; do not chase ceasefire vol crush
5. SLB — $2,000 — Patience (need XOM/CVX capex signal first)
6. GLD calls — $1,500 — Technical (2 consecutive closes above 100-day SMA)

## Exit Signal Status
| # | Signal | Status | Notes |
|---|--------|--------|-------|
| S1 | Shipping insurance | CLEAR | War risk easing with ceasefire |
| S2 | Futures curve | CLEAR | WTI −16% on ceasefire; backwardation flattening |
| S3 | Xi–Trump diplomatic | TRIGGERED | Ceasefire = diplomatic resolution signal (stays until Islamabad outcome) |
| S4 | Iranian pragmatist | TRIGGERED | Ceasefire confirms pragmatist faction influence |
| S5 | Linde/APD force majeure | CLEAR | Ras Laffan structurally still closed |
| S6 | SPR drawdown | CLEAR | SPR release ongoing |
| S7 | Media consensus | CLEAR | Energy bull thesis unwinding with ceasefire |
| S8 | Trump resolution post | TRIGGERED | Ceasefire = resolution equivalent per exit rule |

**3 triggered (S3+S4+S8) → exit rule executed correctly on Apr 8.**
Re-entry requires: ceasefire breakdown + S3 or S8 downgrade to CAUTION/CLEAR.

## Scenario Probabilities (Apr 9 — based on observable reality vs. market optimism)
- A — Resolution (40%): Ceasefire holds, Islamabad talks produce framework, Hormuz conditionally reopens
- B — Partial Resolution (45%, modal): Ceasefire → stalled negotiations → toll regime, partial reopening
- C — Escalation (15%): Ceasefire breaks down post-Apr 22, strikes resume

### Prediction Market Signals (Apr 8)
- Kalshi: Ceasefire holds through April 21 → **26% YES** (very low confidence)
- Polymarket: Hormuz normal traffic by April 30 → ~11-39% (wide range; fragile)
- Polymarket: Hormuz normal traffic by May 31 → 64% YES
- Polymarket: US ends military ops by April 30 → 42% YES
- Kalshi: US-Iran nuclear deal before 2027 → 35%
- Kalshi: US-Iran nuclear deal before August → 19%
- Market-implied scenario: B most likely (toll regime / partial reopening), C risk elevated

**Critical disconnect:** Markets say ceasefire holds (A/B) but Hormuz reopening is slow (C-ish). This is the "False Dawn" scenario — ceasefire without genuine resolution.

## Key Dates
- Apr 10 — CPI report (first post-war inflation read)
- Apr 12 — Islamabad talks (Vance/Witkoff/Kushner + Iran delegation) — PRIMARY BINARY CATALYST
- Apr 21 — NOC earnings (no position, but thesis signal)
- Apr 22 — Ceasefire expiry — primary re-entry decision point
- Apr 28 — RTX earnings (no position)
- Apr 30 — LIN earnings (no position)

## Constraints
- Cannot monitor or act quickly during market hours (pre-set stops/limits only)
- Do not concentrate further in RKLB

## Code State (v0.8)
### Architecture
- `config.py` — source of truth for positions, signals, scenarios, waiting list
- `data.py` — yfinance price fetch; `fetch_option_prices()` returns dict with price+source
- `analysis.py` — P&L calc, prompt builders (build_prompt, build_sync_prompt)
- `components.py` — HTML rendering only
- `app.py` — Streamlit orchestration, Morning Sync panel
- `kalshi.py` — Kalshi + Polymarket live odds (TTL 120s, cache-clear on error)
- `github_state.py` — GitHub Contents API read/write; patch helpers

### Known Issues / Pending Work
- `analysis.py` prompts reference thesis as active with positions; need update to reflect paused state (DONE in prompts — "THESIS STATUS: PAUSED" already in both build_prompt and build_sync_prompt)
- Plans file `.claude/plans/floating-churning-summit-agent-affba7ae9c118998f.md` contains 3 pending fixes (all resolved in v0.8 per code state): TTL reduction ✓, option dict return ✓, dynamic dates ✓
- Ceasefire expiry deadline in `config.py` set to `2026-04-22T20:00:00` — verify this matches official terms

### Config Patching Rules
- Use `re.DOTALL` + `json.dumps()` for safe string embedding
- Avoid `rf''` strings; use plain `r''` + `str()` concatenation
- `patch_scenario_probabilities` uses letter_to_fragment mapping: A/B/C → name substring match
- Always `compile(config_text, "config.py", "exec")` before commit

## Tools
- Dashboard: crisis-monitor-dashboard.streamlit.app
- Repo: notagadget/crisis-monitor-dashboard
- Live prices: https://finance.yahoo.com/portfolio/p_1/view/v1 (Chrome plugin)
- Kalshi API: https://api.elections.kalshi.com/trade-api/v2
- Polymarket: https://polymarket.com/predictions/iran
- Price history: stockanalysis.com/etf/[ticker]/history/

## P&L Framework
Thesis bucket vs Legacy bucket — never netted.
Legacy P&L benchmarked from Mar 30, 2026 (thesis entry date), NOT original cost basis.

## Historical Analog
Transitioning from 1973 (oil weaponized) toward 1979-style negotiated resolution.
Ceasefire = end of Phase 2 (False Dawn). Phase 3 = full resolution OR renewed escalation.
Key differentiator from 1979: nuclear issue + Khamenei assassination + US military still in region.