"""Producer price index (PPI) — monthly, NBS.

Source: ``akshare.macro_china_ppi``. Factory-gate prices for industrial goods.
Stored fields: the year-on-year rate (headline) and the price index (prior-year
month = 100). A long run of negative PPI yoy is the clearest gauge of China's
industrial deflation. Published for January and February separately.

Run from the repo root:  python -m fetch.ppi
"""

from __future__ import annotations

import pandas as pd

from fetch.common import fetch_with_retry, normalize_nbs_monthly, write_indicator

INDICATOR_ID = "ppi"


def transform(raw: pd.DataFrame) -> pd.DataFrame:
    return normalize_nbs_monthly(
        raw, month_col="月份", value_col="当月", yoy_col="当月同比增长",
        ytd_value_col="累计",
    )


def main() -> None:
    import akshare as ak

    raw = fetch_with_retry(ak.macro_china_ppi)
    df = transform(raw)
    write_indicator(
        df,
        INDICATOR_ID,
        source="National Bureau of Statistics",
        source_detail="NBS monthly release, via akshare (EastMoney mirror)",
        akshare_function="macro_china_ppi",
        unit="index (prior-year month = 100)",
        notes=(
            "Producer price index (factory-gate prices). Read by year-on-year "
            "rate; sustained negative readings signal industrial deflation. "
            "'value' is the price index (prior-year month = 100)."
        ),
    )


if __name__ == "__main__":
    main()
