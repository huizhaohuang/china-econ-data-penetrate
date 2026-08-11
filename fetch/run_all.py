"""Run every fetcher in sequence, isolating failures.

Each indicator is fetched independently: one broken endpoint logs an error and
leaves its existing CSV untouched rather than aborting the whole refresh. Run
locally from a China-reachable network:

    python -m fetch.run_all

After the fetch, a freshness report compares each indicator's newest period
against its release calendar (release_day in content/indicators.yaml), so a
feed that lags its publisher is visible immediately - "the July print is not
out yet" and "the feed is behind" are different problems.

The Streamlit app reads the committed CSVs: to update a deployed site, commit
and push data/ after a refresh (see `make publish`).
"""

from __future__ import annotations

import importlib
import json
import sys
from datetime import date

import yaml

from fetch.common import DATA_DIR, ROOT
from fetch.freshness import expected_latest_period

# Module names under fetch/ that expose a main(); order is display order.
FETCHERS = [
    "retail_sales",
    "fixed_asset_investment",
    "fiscal_revenue",
    "new_loans",
    "cpi",
    "ppi",
    "manufacturing_pmi",
    "money_supply",
    "social_financing",
    "trade",
]


def freshness_report(today: date) -> None:
    """Per-indicator data currency versus the release calendar."""
    with open(ROOT / "content" / "indicators.yaml", encoding="utf-8") as fh:
        indicators = (yaml.safe_load(fh) or {}).get("indicators", {})

    print(f"[run_all] freshness report ({today.isoformat()}):", file=sys.stderr)
    behind = []
    for meta_path in sorted(DATA_DIR.glob("*.meta.json")):
        ind_id = meta_path.name.removesuffix(".meta.json")
        try:
            meta = json.loads(meta_path.read_text())
            latest = meta["latest_period"]
            spec = indicators.get(meta.get("indicator_id", ind_id), {})
            release_day = spec.get("release_day")
            if not release_day:
                status = "no release calendar entry"
            else:
                expected = expected_latest_period(
                    today, release_day, spec.get("no_january_release", False),
                    spec.get("december_release_day"))
                if latest >= expected:
                    status = "current"
                else:
                    status = f"BEHIND - {expected} expected by the release calendar"
                    behind.append(ind_id)
        except Exception as exc:  # a broken sidecar must not sink the report
            latest, status = "?", f"unreadable meta ({exc!r})"
        print(f"[run_all]   {ind_id:<24} data through {latest}  ({status})",
              file=sys.stderr)
    if behind:
        print(f"[run_all] behind the calendar: {', '.join(behind)} - the "
              "upstream feed may lag its publisher by a few days; if this "
              "persists, check the akshare function against the source site.",
              file=sys.stderr)


def main() -> int:
    failures = []
    for name in FETCHERS:
        try:
            importlib.import_module(f"fetch.{name}").main()
        except Exception as exc:  # keep going; a bad endpoint must not block the rest
            print(f"[run_all] FAILED {name}: {exc!r}", file=sys.stderr)
            failures.append(name)

    try:
        freshness_report(date.today())
    except Exception as exc:  # the advisory report must never fail the fetch run
        print(f"[run_all] freshness report failed: {exc!r}", file=sys.stderr)

    if failures:
        print(f"[run_all] {len(failures)} failed: {', '.join(failures)}", file=sys.stderr)
        return 1
    print("[run_all] all fetchers succeeded", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
