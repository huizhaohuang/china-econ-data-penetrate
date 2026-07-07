"""General public budget revenue (财政收入) — monthly, MOF.

Source: ``akshare.macro_china_czsr``. Single-month and year-to-date revenue
with year-on-year rates. Read by the year-to-date yoy: fiscal revenue is a
side-read on the economy (weak tax take signals soft corporate profits and
nominal growth). Jan-February are published combined, as with NBS activity data.

Run from the repo root:  python -m fetch.fiscal_revenue
"""

from __future__ import annotations

import pandas as pd

from fetch.common import fetch_with_retry, normalize_nbs_monthly, write_indicator

INDICATOR_ID = "fiscal_revenue"


def transform(raw: pd.DataFrame) -> pd.DataFrame:
    return normalize_nbs_monthly(
        raw, month_col="月份", value_col="当月", yoy_col="当月-同比增长",
        mom_col="当月-环比增长", ytd_value_col="累计", ytd_yoy_col="累计-同比增长",
    )


def main() -> None:
    import akshare as ak

    raw = fetch_with_retry(ak.macro_china_czsr)
    df = transform(raw)
    write_indicator(
        df,
        INDICATOR_ID,
        source="Ministry of Finance",
        source_detail="MOF monthly release, via akshare (EastMoney mirror)",
        akshare_function="macro_china_czsr",
        unit="RMB 100 million",
        notes=(
            "General public budget revenue. Read by year-to-date yoy. January "
            "and February are published combined. Budget expenditure and the "
            "bond-issuance-vs-quota view are tracked separately (planned)."
        ),
    )


if __name__ == "__main__":
    main()
