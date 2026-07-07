"""Run every fetcher in sequence, isolating failures.

Each indicator is fetched independently: one broken endpoint logs an error and
leaves its existing CSV untouched rather than aborting the whole refresh. Run
locally from a China-reachable network:

    python -m fetch.run_all
"""

from __future__ import annotations

import importlib
import sys

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


def main() -> int:
    failures = []
    for name in FETCHERS:
        try:
            importlib.import_module(f"fetch.{name}").main()
        except Exception as exc:  # keep going; a bad endpoint must not block the rest
            print(f"[run_all] FAILED {name}: {exc!r}", file=sys.stderr)
            failures.append(name)
    if failures:
        print(f"[run_all] {len(failures)} failed: {', '.join(failures)}", file=sys.stderr)
        return 1
    print("[run_all] all fetchers succeeded", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
