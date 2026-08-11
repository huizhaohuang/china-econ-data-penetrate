"""Shared plumbing for the fetch scripts.

Every fetcher follows the same contract:

* pull one indicator from akshare, with retries (Chinese official data
  endpoints are unreliable, especially from non-China IPs);
* normalise it to a tidy frame with a first-of-month ISO ``date`` column;
* write ``data/<indicator_id>.csv`` plus a ``.meta.json`` sidecar, so the
  Streamlit app can show data provenance and staleness without making any
  network call at runtime.

The CSVs are committed to git; their history doubles as a data audit trail,
so writers keep column order and float precision stable to produce clean diffs.
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

_NBS_MONTH_RE = re.compile(r"(\d{4})\D+(\d{1,2})\D*月")


def log(msg: str) -> None:
    print(f"[fetch] {msg}", file=sys.stderr)


def fetch_with_retry(fetch_fn: Callable[[], pd.DataFrame], *, attempts: int = 4,
                     base_delay: float = 5.0) -> pd.DataFrame:
    """Call an akshare function with exponential backoff.

    Raises the last exception if every attempt fails, so a broken fetch can
    never silently overwrite a good CSV.
    """
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            df = fetch_fn()
            if df is None or len(df) == 0:
                raise ValueError("source returned an empty frame")
            return df
        except Exception as exc:  # akshare raises a wide mix of exception types
            last_error = exc
            if attempt < attempts:
                delay = base_delay * 2 ** (attempt - 1)
                log(f"attempt {attempt}/{attempts} failed ({exc!r}); retrying in {delay:.0f}s")
                time.sleep(delay)
    raise RuntimeError(f"all {attempts} fetch attempts failed") from last_error


def parse_nbs_month(raw: str) -> str:
    """Convert an NBS-style month label ('2026年05月份') to '2026-05-01'."""
    match = _NBS_MONTH_RE.search(str(raw))
    if not match:
        raise ValueError(f"unrecognised month label: {raw!r}")
    year, month = int(match.group(1)), int(match.group(2))
    if not 1 <= month <= 12:
        raise ValueError(f"month out of range in label: {raw!r}")
    return f"{year:04d}-{month:02d}-01"


def normalize_nbs_monthly(raw: pd.DataFrame, *, month_col: str, value_col: str,
                          yoy_col: str, ytd_value_col: str | None = None,
                          mom_col: str | None = None,
                          ytd_yoy_col: str | None = None) -> pd.DataFrame:
    """Normalise an EastMoney/NBS 月份-style monthly frame to the project's
    standard columns: date, value, yoy, mom, ytd_value, ytd_yoy,
    jan_feb_combined.

    Many NBS activity series share this layout (single-month value + yoy,
    year-to-date value + yoy) and the same Chinese New Year quirk: NBS
    publishes January and February combined, so the February row carries only
    the cumulative figures and the single-month value/yoy are blank. That
    February row is flagged ``jan_feb_combined``; nothing is interpolated.
    Absent optional columns are emitted as NaN so every indicator CSV has the
    same schema.
    """
    out = pd.DataFrame({
        "date": raw[month_col].map(parse_nbs_month),
        "value": pd.to_numeric(raw[value_col], errors="coerce").round(1),
        "yoy": pd.to_numeric(raw[yoy_col], errors="coerce").round(1),
    })
    out["mom"] = (pd.to_numeric(raw[mom_col], errors="coerce").round(2)
                  if mom_col else pd.NA)
    out["ytd_value"] = (pd.to_numeric(raw[ytd_value_col], errors="coerce").round(1)
                        if ytd_value_col else pd.NA)
    out["ytd_yoy"] = (pd.to_numeric(raw[ytd_yoy_col], errors="coerce").round(1)
                      if ytd_yoy_col else pd.NA)

    out = out.sort_values("date").reset_index(drop=True)
    month = out["date"].str.slice(5, 7)
    has_ytd = out["ytd_value"].notna() if ytd_value_col else False
    out["jan_feb_combined"] = (month == "02") & out["value"].isna() & has_ytd
    return out


def merge_with_existing(df: pd.DataFrame, csv_path: Path) -> tuple[pd.DataFrame, int, int]:
    """Merge a freshly fetched frame with the committed CSV, if one exists.

    Sources occasionally shorten the history window they return (EastMoney
    trimmed FAI from 2008 to 2012 in Aug 2026, and recomputes yoy within
    the window, blanking its first year); a plain overwrite would then
    silently degrade committed data. Fetched values win, so revisions
    propagate; months the source no longer returns, and cells it now leaves
    blank, are retained from the existing CSV. Returns the merged frame,
    the count of retained months and the count of backfilled cells.
    """
    if not csv_path.exists():
        return df, 0, 0
    prev = pd.read_csv(csv_path, dtype={"date": str}).set_index("date")
    prev = prev.reindex(columns=[c for c in df.columns if c != "date"])
    new = df.set_index("date")

    overlap = new.index.intersection(prev.index)
    # Cells the fetched frame blanks BY DESIGN must not be backfilled: a
    # jan_feb_combined row's value/yoy/mom are intentionally empty, and
    # refilling them would commit a flagged-combined row carrying a
    # single-month value. Mask them out of prev before merging.
    if "jan_feb_combined" in new.columns:
        flagged = overlap[new.loc[overlap, "jan_feb_combined"].astype(bool)]
        cols = [c for c in ("value", "yoy", "mom") if c in prev.columns]
        prev.loc[flagged, cols] = pd.NA

    n_retained = len(prev.index.difference(new.index))
    n_backfilled = int((new.loc[overlap].isna() & prev.loc[overlap].notna())
                       .to_numpy().sum())
    if not n_retained and not n_backfilled:
        return df, 0, 0
    merged = new.combine_first(prev).reset_index()
    return merged[df.columns.tolist()], n_retained, n_backfilled


def write_indicator(df: pd.DataFrame, indicator_id: str, *, source: str,
                    source_detail: str, akshare_function: str, unit: str,
                    notes: str = "") -> None:
    """Write the indicator CSV and its meta sidecar.

    Expects a ``date`` column of ISO first-of-month strings; sorts ascending
    and validates uniqueness before writing. Months present in the committed
    CSV but absent from the fetched frame are retained rather than deleted
    (see merge_with_existing).
    """
    if "date" not in df.columns:
        raise ValueError("indicator frame must have a 'date' column")
    if df["date"].duplicated().any():
        dupes = df.loc[df["date"].duplicated(), "date"].tolist()
        raise ValueError(f"duplicate months in {indicator_id}: {dupes}")

    DATA_DIR.mkdir(exist_ok=True)
    csv_path = DATA_DIR / f"{indicator_id}.csv"
    df, n_retained, n_backfilled = merge_with_existing(df, csv_path)
    if n_retained or n_backfilled:
        log(f"{indicator_id}: source no longer returns {n_retained} committed "
            f"month(s) / {n_backfilled} cell(s); retaining them from the "
            f"existing CSV")

    df = df.sort_values("date").reset_index(drop=True)
    df.to_csv(csv_path, index=False)

    meta = {
        "indicator_id": indicator_id,
        "source": source,
        "source_detail": source_detail,
        "akshare_function": akshare_function,
        "unit": unit,
        "fetched_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rows": len(df),
        "first_period": df["date"].iloc[0][:7],
        "latest_period": df["date"].iloc[-1][:7],
        "columns": list(df.columns),
        "notes": notes,
    }
    if n_retained:
        meta["rows_retained_from_prior_csv"] = n_retained
    meta_path = DATA_DIR / f"{indicator_id}.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")

    log(f"wrote {csv_path.name} ({len(df)} rows, {meta['first_period']} to "
        f"{meta['latest_period']}) and {meta_path.name}")
