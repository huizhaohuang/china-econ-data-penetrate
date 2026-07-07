"""Consumer price index (CPI) — monthly, NBS.

Source: ``akshare.macro_china_cpi`` (national series). Stored fields: the
year-on-year rate (the headline), the month-on-month rate, and the price index
itself (prior-year month = 100, so 101.2 means +1.2% yoy). Unlike NBS activity
data, CPI is published for January and February separately, so there is no
combined-month gap.

Run from the repo root:  python -m fetch.cpi
"""

from __future__ import annotations

import pandas as pd

from fetch.common import fetch_with_retry, normalize_nbs_monthly, write_indicator

INDICATOR_ID = "cpi"


def transform(raw: pd.DataFrame) -> pd.DataFrame:
    return normalize_nbs_monthly(
        raw, month_col="月份", value_col="全国-当月", yoy_col="全国-同比增长",
        mom_col="全国-环比增长", ytd_value_col="全国-累计",
    )


def main() -> None:
    import akshare as ak

    raw = fetch_with_retry(ak.macro_china_cpi)
    df = transform(raw)
    write_indicator(
        df,
        INDICATOR_ID,
        source="National Bureau of Statistics",
        source_detail="NBS monthly release, via akshare (EastMoney mirror)",
        akshare_function="macro_china_cpi",
        unit="index (prior-year month = 100)",
        notes=(
            "National CPI. Read by year-on-year rate. 'value' is the price index "
            "(prior-year month = 100); yoy restates it as a percentage change. "
            "Published for January and February separately (no combined-month gap)."
        ),
    )


if __name__ == "__main__":
    main()
