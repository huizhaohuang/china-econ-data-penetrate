"""Total social financing — monthly increment (社会融资规模增量) — PBOC.

Source: ``akshare.macro_china_shrzgm``. The broadest measure of new credit to
the real economy in a month, plus its largest component, new RMB loans. This is
a flow (new financing added that month), not a stock or a growth rate, so it is
read as a level against prior months and the same month a year earlier. The
stock year-on-year growth is not in this feed.

Run from the repo root:  python -m fetch.social_financing
"""

from __future__ import annotations

import pandas as pd

from fetch.common import fetch_with_retry, write_indicator

INDICATOR_ID = "social_financing"


def _parse_yyyymm(raw: str) -> str:
    s = str(raw).strip()
    return f"{s[:4]}-{s[4:6]}-01"


def transform(raw: pd.DataFrame) -> pd.DataFrame:
    # astype(float): the source sometimes delivers all-integer vintages, and a
    # dtype flip between fetches would churn the CSV formatting (audit trail).
    df = pd.DataFrame({
        "date": raw["月份"].map(_parse_yyyymm),
        "value": pd.to_numeric(raw["社会融资规模增量"], errors="coerce").astype(float).round(1),
        "rmb_loans": pd.to_numeric(raw["其中-人民币贷款"], errors="coerce").astype(float).round(1),
    })
    return df.sort_values("date").reset_index(drop=True)


def main() -> None:
    import akshare as ak

    raw = fetch_with_retry(ak.macro_china_shrzgm)
    df = transform(raw)
    write_indicator(
        df,
        INDICATOR_ID,
        source="People's Bank of China",
        source_detail="PBOC monthly release, via akshare (EastMoney mirror)",
        akshare_function="macro_china_shrzgm",
        unit="RMB 100 million (monthly increment)",
        notes=(
            "Total social financing monthly increment ('value') and its new RMB "
            "loan component ('rmb_loans'). A flow, not a stock: read against "
            "prior months and the year-earlier month. Heavily seasonal, with a "
            "large January print each year. Stock yoy is not in this feed."
        ),
    )


if __name__ == "__main__":
    main()
