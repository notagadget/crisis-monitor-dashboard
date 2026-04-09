COMPLETED
✓ Fix Polymarket data pull: keyword-relevance filtering now implemented (THESIS_KEYWORDS in kalshi.py)
✓ Fix Kalshi data pull: keyword-relevance filtering now returns Iran markets dynamically
✓ Scenario ordering: SCENARIOS order in config.py is correct (A 45%, B 40%, C 15%)

TO DO — HIGH PRIORITY
- Add patch_waiting_list() to github_state.py so Morning Sync can commit waiting list changes
- Add patch_deadline_iso() to github_state.py for DEADLINE_ISO (critical with serial extensions)
- Add patch_calendar() to github_state.py
- Wire up new patch functions into commit flow in app.py (lines 348-384)

TO DO — MEDIUM PRIORITY
- Scenario display: visually separate "current evidence / odds" from "expected outcome" per scenario card
- GUI polish: Exit Signals could use horizontal layout option for space efficiency

TO DO — LOW PRIORITY / NICE TO HAVE
- Enforce scenario sort order in code (sort SCENARIOS by pct descending before rendering)
- DAY_SUMMARY label: auto-increment day number in Morning Sync instead of relying on Claude to count correctly