IN PROGRESS / PARTIAL
- Scenario ordering: config order is correct but no code enforces sort; manual discipline required on each Morning Sync commit

TO DO — HIGH PRIORITY
- Fix Polymarket data pull: gamma-api keyword "hormuz" is not returning the specific Iran markets
  (US forces enter Iran, ceasefire, Kharg strike). Target slugs from Context.md directly.
- Fix Kalshi data pull: series_ticker KXIRAN likely invalid; use known event/market ticker
  pattern (series → event → market). Recession market (KXUSRECESSION) needs verification too.
- Add patch_waiting_list() to github_state.py so Morning Sync can commit waiting list changes
- Add patch_deadline_iso() to github_state.py for DEADLINE_ISO (critical with serial extensions)
- Add patch_calendar() to github_state.py

TO DO — MEDIUM PRIORITY
- GUI: move exit signals to horizontal layout
- GUI: move Morning Sync and Run AI Analysis sections to bottom of page
- Scenario display: visually separate "current evidence / odds" from "expected outcome" per scenario card
- Morning Sync: wire up the new patch functions (waiting list, deadline, calendar) into commit flow in app.py

TO DO — LOW PRIORITY / NICE TO HAVE
- Enforce scenario sort order in code (sort SCENARIOS by pct descending before rendering)
- DAY_SUMMARY label: auto-increment day number in Morning Sync instead of relying on Claude to count correctly