"""
github_state.py — read and write config.py via the GitHub Contents API.
Never stores credentials; callers pass token explicitly.
"""

import base64
import re
import requests
from datetime import date

GITHUB_API = "https://api.github.com"


# ── READ ──────────────────────────────────────────────────────────────────────

def get_config_sha(repo: str, token: str) -> tuple[str, str]:
    """
    Returns (raw_content, sha) of config.py from the repo.
    Raises on any HTTP error.
    """
    url = f"{GITHUB_API}/repos/{repo}/contents/config.py"
    r = requests.get(url, headers=_headers(token), timeout=10)
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


# ── WRITE ─────────────────────────────────────────────────────────────────────

def commit_config(repo: str, token: str, new_content: str, sha: str,
                  message: str = None) -> bool:
    """
    Commits new_content as config.py. Returns True on success.
    sha must match the current file sha (prevents blind overwrites).
    """
    if message is None:
        message = f"Morning Sync update {date.today().isoformat()}"
    url = f"{GITHUB_API}/repos/{repo}/contents/config.py"
    payload = {
        "message": message,
        "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8"),
        "sha": sha,
    }
    r = requests.put(url, json=payload, headers=_headers(token), timeout=15)
    r.raise_for_status()
    return True


# ── PATCH HELPERS ─────────────────────────────────────────────────────────────
# These surgically replace sections in config.py without touching anything else.

def patch_day_summary(config_text: str, label: str, body: str) -> str:
    """Replace DAY_SUMMARY dict in config.py with new label + body."""
    # Escape any backslashes or quotes in body for safe embedding
    body_escaped = body.replace("\\", "\\\\").replace('"', '\\"')
    new_block = (
        'DAY_SUMMARY = {\n'
        f'    "label": "{label}",\n'
        f'    "body": (\n'
        f'        "{body_escaped}"\n'
        '    ),\n'
        '}'
    )
    # Replace from DAY_SUMMARY = { to the closing }
    pattern = r'DAY_SUMMARY\s*=\s*\{[^}]*(?:\([^)]*\)[^}]*)?\}'
    result = re.sub(pattern, new_block, config_text, flags=re.DOTALL)
    return result


def patch_signal_defaults(config_text: str, signals: dict) -> str:
    """Replace SIGNAL_DEFAULTS dict values with new signal states."""
    def replace_signal(m):
        sid = m.group(1)
        comment = m.group(3) or ""
        new_val = signals.get(sid, int(m.group(2)))
        return f'    "{sid}": {new_val},{comment}'

    pattern = r'    "([s]\d+)":\s*(\d)(.*)'
    result = re.sub(pattern, replace_signal, config_text)
    return result


def patch_waiting_list_status(config_text: str, ticker: str, new_status: str,
                               new_when: str = None, new_cond: str = None) -> str:
    """
    Update the status (and optionally when/cond) for a single waiting list entry.
    Matches on ticker string — safe for multi-ticker entries like 'XOM / CVX'.
    """
    # Find the block for this ticker and update status
    escaped = re.escape(ticker)
    if new_when and new_cond:
        pattern = (
            rf'(\{{"ticker": "{escaped}",\s*"status": ")[^"]+(",\s*"when": ")[^"]+(",\s*"cond": ")[^"]+'
        )
        replacement = rf'\g<1>{new_status}\g<2>{new_when}\g<3>{new_cond}'
    else:
        pattern = rf'(\{{"ticker": "{escaped}",\s*"status": ")[^"]+'
        replacement = rf'\g<1>{new_status}'
    return re.sub(pattern, replacement, config_text)


# ── INTERNAL ──────────────────────────────────────────────────────────────────

def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
