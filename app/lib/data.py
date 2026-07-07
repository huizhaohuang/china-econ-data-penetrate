"""Read-only access to the committed CSVs in data/.

The app never fetches anything at runtime: data/ is the single source of
truth, refreshed locally by the fetch/ scripts and committed to git. Caches
are keyed on file mtime so a fresh fetch shows up on the next rerun.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
NOTES_DIR = ROOT / "content" / "notes"


@st.cache_data(show_spinner=False)
def _read_csv(path: str, mtime: float) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["date"])


@st.cache_data(show_spinner=False)
def _read_meta(path: str, mtime: float) -> dict:
    return json.loads(Path(path).read_text())


def available_indicators() -> set[str]:
    if not DATA_DIR.exists():
        return set()
    return {p.stem for p in DATA_DIR.glob("*.csv")}


def load_indicator(indicator_id: str) -> tuple[pd.DataFrame | None, dict | None]:
    csv_path = DATA_DIR / f"{indicator_id}.csv"
    meta_path = DATA_DIR / f"{indicator_id}.meta.json"
    if not csv_path.exists():
        return None, None
    df = _read_csv(str(csv_path), csv_path.stat().st_mtime)
    meta = None
    if meta_path.exists():
        meta = _read_meta(str(meta_path), meta_path.stat().st_mtime)
    return df, meta


def _num(v) -> float | None:
    return None if v is None or pd.isna(v) else float(v)


def latest_reading(df: pd.DataFrame, overview: dict) -> dict:
    """Headline reading for an overview tile, driven by the indicator's
    ``metric.overview`` spec so one code path serves every indicator kind
    (year-on-year rates, diffusion indices, monthly flows).

    ``overview`` keys used:
      col            headline column (e.g. yoy, m2_yoy, value)
      period_label   text before the period (e.g. "YoY", "index", "new")
      combined_col   optional: use this when the latest row is a Jan-Feb
                     combined print (e.g. ytd_yoy), with combined_label
                     (and combined_kind, applied by the tile renderer)
      level_col      optional secondary level line
      delta_mode     3m_avg (default) | same_month_last_year | none.
                     Raw seasonal flows (e.g. new social financing, with its
                     huge January print) must not be differenced against the
                     trailing months - compare them to the same month a year
                     earlier, or not at all.

    The default delta is the headline minus the mean of the three prior
    published values of the same column - and is suppressed for a combined
    print, whose basis differs from the single-month history and must never be
    differenced against it silently.
    """
    col = overview["col"]
    last = df.iloc[-1]
    has_flag = "jan_feb_combined" in df.columns
    combined = bool(last.get("jan_feb_combined", False)) if has_flag else False
    delta_mode = overview.get("delta_mode", "3m_avg")

    if combined and overview.get("combined_col"):
        headline = last[overview["combined_col"]]
        label = overview.get("combined_label", overview.get("period_label", ""))
        delta = None
        level = None
    else:
        headline = last[col]
        label = overview.get("period_label", "")
        delta = None
        if pd.notna(headline) and delta_mode == "3m_avg":
            prior = df.iloc[:-1][col].dropna().tail(3)
            if len(prior) == 3:
                delta = round(float(headline - prior.mean()), 1)
        elif pd.notna(headline) and delta_mode == "same_month_last_year":
            year_ago = last["date"] - pd.DateOffset(years=1)
            match = df.loc[df["date"] == year_ago, col].dropna()
            if len(match):
                delta = round(float(headline - match.iloc[0]), 1)
        level_col = overview.get("level_col")
        level = last[level_col] if level_col else None

    return {
        "period": last["date"],
        "headline": _num(headline),
        "period_label": label,
        "level": _num(level),
        "delta_vs_prior": delta,
        "delta_mode": delta_mode,
        "jan_feb_combined": combined,
    }


def fetched_at(meta: dict | None) -> datetime | None:
    if not meta or "fetched_at_utc" not in meta:
        return None
    return datetime.strptime(meta["fetched_at_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )


def days_since_fetch(meta: dict | None) -> int | None:
    ts = fetched_at(meta)
    if ts is None:
        return None
    return (datetime.now(timezone.utc) - ts).days


@st.cache_data(show_spinner=False)
def _read_notes(paths_key: str) -> list[dict]:
    notes = []
    for path in sorted(NOTES_DIR.glob("*.md"), reverse=True):
        notes.append({"name": path.stem, "body": path.read_text(encoding="utf-8")})
    return notes


def list_notes() -> list[dict]:
    """Monthly notes as {name, body}, newest first by filename. Cache is keyed
    on the set of files and their mtimes so edits show on the next rerun."""
    if not NOTES_DIR.exists():
        return []
    key = ",".join(f"{p.name}:{p.stat().st_mtime}"
                   for p in sorted(NOTES_DIR.glob("*.md")))
    return _read_notes(key)
