"""Retail sales of consumer goods (社会消费品零售总额) — monthly, NBS.

Source function: ``akshare.macro_china_consumer_goods_retail`` (EastMoney
mirror of NBS releases). Source columns: month label, single-month value
(RMB 100 million), single-month yoy %, mom %, year-to-date value, ytd yoy %.

NBS publishes January and February combined: in recent years there is no
January release and the February row carries only the Jan–Feb cumulative
figures (single-month value/yoy are absent, and March has no mom either).
That structure is kept as-is — ``jan_feb_combined`` flags such February
rows and nothing is ever interpolated.

Run from the repo root:  python -m fetch.retail_sales
"""

from __future__ import annotations

import pandas as pd

from fetch.common import fetch_with_retry, normalize_nbs_monthly, write_indicator

INDICATOR_ID = "retail_sales"


def transform(raw: pd.DataFrame) -> pd.DataFrame:
    return normalize_nbs_monthly(
        raw, month_col="月份", value_col="当月", yoy_col="同比增长",
        mom_col="环比增长", ytd_value_col="累计", ytd_yoy_col="累计-同比增长",
    )


def main() -> None:
    import akshare as ak

    raw = fetch_with_retry(ak.macro_china_consumer_goods_retail)
    df = transform(raw)
    write_indicator(
        df,
        INDICATOR_ID,
        source="National Bureau of Statistics",
        source_detail="NBS monthly release, via akshare (EastMoney mirror)",
        akshare_function="macro_china_consumer_goods_retail",
        unit="RMB 100 million",
        notes=(
            "January and February are published combined by NBS: February rows "
            "flagged jan_feb_combined carry only ytd_value/ytd_yoy (covering "
            "Jan-Feb together); value, yoy and the following March mom are "
            "intentionally empty for those periods."
        ),
    )


if __name__ == "__main__":
    main()
