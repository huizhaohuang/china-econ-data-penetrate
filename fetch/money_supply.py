"""Money supply — M1 and M2 (货币供应量) — monthly, PBOC.

Source: ``akshare.macro_china_money_supply``. Broad money (M2) and narrow money
(M1), each as a stock and a year-on-year growth rate. The M1-M2 gap is closely
watched: narrow money weakening relative to broad money points to cash being
parked rather than deployed. Read by year-on-year growth.

Run from the repo root:  python -m fetch.money_supply
"""

from __future__ import annotations

import pandas as pd

from fetch.common import fetch_with_retry, parse_nbs_month, write_indicator

INDICATOR_ID = "money_supply"


def transform(raw: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({
        "date": raw["月份"].map(parse_nbs_month),
        "m2_yoy": pd.to_numeric(raw["货币和准货币(M2)-同比增长"], errors="coerce").round(1),
        "m1_yoy": pd.to_numeric(raw["货币(M1)-同比增长"], errors="coerce").round(1),
        "m2_level": pd.to_numeric(raw["货币和准货币(M2)-数量(亿元)"], errors="coerce").round(1),
        "m1_level": pd.to_numeric(raw["货币(M1)-数量(亿元)"], errors="coerce").round(1),
    })
    return df.sort_values("date").reset_index(drop=True)


def main() -> None:
    import akshare as ak

    raw = fetch_with_retry(ak.macro_china_money_supply)
    df = transform(raw)
    write_indicator(
        df,
        INDICATOR_ID,
        source="People's Bank of China",
        source_detail="PBOC monthly release, via akshare (EastMoney mirror)",
        akshare_function="macro_china_money_supply",
        unit="yoy % (m*_yoy); RMB 100 million (m*_level)",
        notes=(
            "M2 and M1 year-on-year growth (m2_yoy, m1_yoy) and stock levels "
            "(m2_level, m1_level). Watch the M1-M2 gap: M1 lagging M2 signals "
            "idle liquidity. Published for January and February separately."
        ),
    )


if __name__ == "__main__":
    main()
