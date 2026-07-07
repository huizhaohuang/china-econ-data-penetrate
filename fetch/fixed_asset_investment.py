"""Fixed asset investment (固定资产投资) — monthly, NBS.

Source: ``akshare.macro_china_gdzctz`` (EastMoney mirror of NBS). NBS publishes
FAI natively as a year-to-date figure; this feed also carries a source-derived
single-month value and its year-on-year rate, which are noisier. It does NOT
carry a year-to-date yoy column, and NBS revises the prior-year base, so a
year-to-date yoy is deliberately left blank rather than recomputed from levels
(that would not match NBS's published headline).

The manufacturing / infrastructure / real-estate breakdown the framework wants
is not in this free feed and is tracked separately (planned).

Run from the repo root:  python -m fetch.fixed_asset_investment
"""

from __future__ import annotations

import pandas as pd

from fetch.common import fetch_with_retry, normalize_nbs_monthly, write_indicator

INDICATOR_ID = "fixed_asset_investment"


def transform(raw: pd.DataFrame) -> pd.DataFrame:
    # No cumulative-yoy column in this feed; ytd_yoy stays blank on purpose.
    return normalize_nbs_monthly(
        raw, month_col="月份", value_col="当月", yoy_col="同比增长",
        mom_col="环比增长", ytd_value_col="自年初累计",
    )


def main() -> None:
    import akshare as ak

    raw = fetch_with_retry(ak.macro_china_gdzctz)
    df = transform(raw)
    write_indicator(
        df,
        INDICATOR_ID,
        source="National Bureau of Statistics",
        source_detail="NBS monthly release, via akshare (EastMoney mirror)",
        akshare_function="macro_china_gdzctz",
        unit="RMB 100 million",
        notes=(
            "NBS publishes FAI as a year-to-date figure; value and yoy here are "
            "the source's single-month derivation and are noisy. ytd_yoy is left "
            "blank because NBS revises the prior-year base, so it cannot be "
            "reproduced from the cumulative levels. Jan-Feb combined per the "
            "usual NBS convention."
        ),
    )


if __name__ == "__main__":
    main()
