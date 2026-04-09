COMPLETED
✓ Fix Polymarket data pull: keyword-relevance filtering now implemented (THESIS_KEYWORDS in kalshi.py)
✓ Fix Kalshi data pull: keyword-relevance filtering now returns Iran markets dynamically
✓ Scenario ordering: SCENARIOS order in config.py is correct (A 45%, B 40%, C 15%)
✓ Add patch_waiting_list() to github_state.py — atomically replaces WAITING_LIST block with 5-key structure
✓ Add patch_deadline_iso() to github_state.py — updates DEADLINE_ISO for ceasefire extensions
✓ Add patch_calendar() to github_state.py — atomically replaces CALENDAR with crit conversion
✓ Extend JSON schema in analysis.py — deadline_extension & calendar_updates fields for Claude responses
✓ Add waiting list approval UI in app.py — checkboxes per item with current → suggested status transitions
✓ Add deadline/calendar review UI in app.py — informational display of extensions and event updates
✓ Wire up 3 patch functions into commit flow in app.py — integrated with waiting list merge logic
✓ Sort scenarios by pct descending in components.py — highest probability displays first
✓ Auto-increment day number in analysis.py — extracts Day N, increments in JSON template

TO DO — MEDIUM PRIORITY
- Scenario display: visually separate "current evidence / odds" from "expected outcome" per scenario card
- GUI polish: Exit Signals could use horizontal layout option for space efficiency

TO DO — LOW PRIORITY / NICE TO HAVE
- (none currently)