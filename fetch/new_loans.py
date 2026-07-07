"""New RMB loans (新增人民币贷款) — monthly, PBOC.

Source: ``akshare.macro_china_new_financial_credit``. Monthly new bank lending
to the real economy, with year-to-date totals. This is the aggregate new-loans
figure; the corporate medium-and-long-term breakdown the framework wants is not
separable in the free feed, so this stands in as the headline credit-flow gauge
and is cross-read with total social financing.

Run from the repo root:  python -m fetch.new_loans
"""

from __future__ import annotations

import pandas as pd

from fetch.common import fetch_with_retry, normalize_nbs_monthly, write_indicator

INDICATOR_ID = "new_loans"


def transform(raw: pd.DataFrame) -> pd.DataFrame:
    return normalize_nbs_monthly(
        raw, month_col="月份", value_col="当月", yoy_col="当月-同比增长",
        mom_col="当月-环比增长", ytd_value_col="累计", ytd_yoy_col="累计-同比增长",
    )


def main() -> None:
    import akshare as ak

    raw = fetch_with_retry(ak.macro_china_new_financial_credit)
    df = transform(raw)
    write_indicator(
        df,
        INDICATOR_ID,
        source="People's Bank of China",
        source_detail="PBOC monthly release, via akshare (EastMoney mirror)",
        akshare_function="macro_china_new_financial_credit",
        unit="RMB 100 million",
        notes=(
            "Aggregate new RMB loans to the real economy. The corporate "
            "medium-and-long-term loan breakdown is not available in the free "
            "feed. Single-month values are volatile and heavily seasonal; read "
            "the year-to-date total and cross-read with total social financing."
        ),
    )


if __name__ == "__main__":
    main()
