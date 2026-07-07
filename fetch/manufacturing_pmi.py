"""Manufacturing PMI (制造业采购经理指数) — monthly, NBS.

Source: ``akshare.macro_china_pmi``. A diffusion index where 50 marks the line
between expansion and contraction, so it is read as a level against 50, not as
a growth rate. The non-manufacturing PMI is carried alongside for context. The
new-export-orders and construction sub-indices the framework wants are not in
this feed (planned).

Run from the repo root:  python -m fetch.manufacturing_pmi
"""

from __future__ import annotations

import pandas as pd

from fetch.common import fetch_with_retry, parse_nbs_month, write_indicator

INDICATOR_ID = "manufacturing_pmi"


def transform(raw: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame({
        "date": raw["月份"].map(parse_nbs_month),
        "value": pd.to_numeric(raw["制造业-指数"], errors="coerce").round(1),
        "nonmfg": pd.to_numeric(raw["非制造业-指数"], errors="coerce").round(1),
    })
    return df.sort_values("date").reset_index(drop=True)


def main() -> None:
    import akshare as ak

    raw = fetch_with_retry(ak.macro_china_pmi)
    df = transform(raw)
    write_indicator(
        df,
        INDICATOR_ID,
        source="National Bureau of Statistics",
        source_detail="NBS monthly release, via akshare (EastMoney mirror)",
        akshare_function="macro_china_pmi",
        unit="diffusion index (50 = no change)",
        notes=(
            "Manufacturing PMI ('value') and non-manufacturing PMI ('nonmfg'), "
            "both diffusion indices read against the 50 expansion/contraction "
            "line. Released on the last day of the reference month, ahead of the "
            "hard activity data."
        ),
    )


if __name__ == "__main__":
    main()
