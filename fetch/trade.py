"""Customs exports and imports (海关进出口) — monthly, GACC.

Source: ``akshare.macro_china_hgjck`` (customs). One fetch yields both sides of
the trade account; this writes two indicators, ``exports`` and ``imports``,
each with a single-month value (converted to USD billion) and year-on-year
rate plus year-to-date figures.

Unlike NBS activity data, this feed carries separate January and February
values every year (GACC's headline release is combined, but the feed reports
monthly figures), so ``jan_feb_combined`` never fires here. The standalone
Jan/Feb single-month rates are Chinese New Year-distorted — the app's copy
directs readers to the year-to-date basis for those months.

Run from the repo root:  python -m fetch.trade
"""

from __future__ import annotations

import pandas as pd

from fetch.common import fetch_with_retry, normalize_nbs_monthly, write_indicator

# Source values are in thousands of USD; convert to USD billion.
_THOUSAND_USD_TO_BILLION = 1e-6


def _side(raw: pd.DataFrame, *, value_col: str, yoy_col: str, mom_col: str,
          ytd_value_col: str, ytd_yoy_col: str) -> pd.DataFrame:
    df = normalize_nbs_monthly(
        raw, month_col="月份", value_col=value_col, yoy_col=yoy_col,
        mom_col=mom_col, ytd_value_col=ytd_value_col, ytd_yoy_col=ytd_yoy_col,
    )
    df["value"] = (df["value"] * _THOUSAND_USD_TO_BILLION).round(1)
    df["ytd_value"] = (df["ytd_value"] * _THOUSAND_USD_TO_BILLION).round(1)
    return df


def main() -> None:
    import akshare as ak

    raw = fetch_with_retry(ak.macro_china_hgjck)

    common = dict(
        source="General Administration of Customs",
        source_detail="GACC monthly release, via akshare (EastMoney mirror)",
        akshare_function="macro_china_hgjck",
        unit="USD billion",
    )

    exports = _side(raw, value_col="当月出口额-金额", yoy_col="当月出口额-同比增长",
                    mom_col="当月出口额-环比增长", ytd_value_col="累计出口额-金额",
                    ytd_yoy_col="累计出口额-同比增长")
    write_indicator(exports, "exports", notes=(
        "Merchandise exports in USD terms. Read by year-on-year rate. Values "
        "converted from the source unit of thousand USD to USD billion. This "
        "feed reports January and February separately (GACC's headline release "
        "combines them); their single-month rates are Chinese New Year-"
        "distorted, so prefer the ytd basis for early-year months."), **common)

    imports = _side(raw, value_col="当月进口额-金额", yoy_col="当月进口额-同比增长",
                    mom_col="当月进口额-环比增长", ytd_value_col="累计进口额-金额",
                    ytd_yoy_col="累计进口额-同比增长")
    write_indicator(imports, "imports", notes=(
        "Merchandise imports in USD terms. Read by year-on-year rate; import "
        "weakness often signals soft domestic demand as much as commodity "
        "prices. Values converted from thousand USD to USD billion. This feed "
        "reports January and February separately (GACC's headline release "
        "combines them); their single-month rates are Chinese New Year-"
        "distorted, so prefer the ytd basis for early-year months."), **common)


if __name__ == "__main__":
    main()
