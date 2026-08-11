"""Data-currency status for the app, from the shared release calendar.

Reuses the expectation logic in fetch/freshness.py - the one fetch module
the app may import, because it is dependency-free by contract (the app must
stay runnable without akshare and the other fetch requirements).
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fetch.freshness import expected_latest_period, release_due_date  # noqa: E402


def currency_status(spec: dict, meta: dict | None) -> dict | None:
    """Compare an indicator's newest period against its release calendar.

    Returns None when the indicator has no release_day or no meta sidecar;
    otherwise {'latest': 'YYYY-MM', 'expected': 'YYYY-MM', 'behind': bool,
    'cause': None | 'feed' | 'stale_fetch'}. 'behind' means a print the
    calendar says is public is not in the data; 'cause' attributes it -
    'feed' when the data was fetched after the print was due (so the
    upstream feed lags its publisher), 'stale_fetch' when the fetch itself
    predates the due date (the panel's data needs a refresh).
    """
    release_day = spec.get("release_day")
    latest = (meta or {}).get("latest_period")
    if not latest or not release_day:
        return None
    december_day = spec.get("december_release_day")
    expected = expected_latest_period(
        date.today(), release_day, spec.get("no_january_release", False),
        december_day)
    behind = latest < expected
    cause = None
    if behind:
        cause = "stale_fetch"
        try:
            fetched = datetime.strptime(
                meta["fetched_at_utc"], "%Y-%m-%dT%H:%M:%SZ").date()
            if fetched >= release_due_date(expected, release_day, december_day):
                cause = "feed"
        except (KeyError, ValueError):
            pass
    return {"latest": latest, "expected": expected, "behind": behind,
            "cause": cause}
