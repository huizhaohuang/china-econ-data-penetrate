"""Small display formatters shared across pages."""

from __future__ import annotations

from datetime import datetime

import pandas as pd


def fmt_month(ts) -> str:
    return pd.Timestamp(ts).strftime("%b %Y")


def fmt_day(dt: datetime | None) -> str:
    if dt is None:
        return "unknown"
    return f"{dt.day} {dt.strftime('%b %Y')}"


def fmt_pct(value: float | None, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "–"
    return f"{value:+.{digits}f}%"


def fmt_trillion(value_100mn: float | None, digits: int = 2) -> str:
    """Format a value given in the official RMB 100 million unit as trillion."""
    if value_100mn is None or pd.isna(value_100mn):
        return "–"
    return f"RMB {value_100mn / 1e4:,.{digits}f} tn"


def fmt_value(v: float | None, kind: str) -> str:
    """Format a headline reading by its measurement kind."""
    if v is None or pd.isna(v):
        return "–"
    if kind == "pct":
        return f"{v:+.1f}%"
    if kind == "index":
        return f"{v:.1f}"
    if kind == "trillion":
        return f"RMB {v / 1e4:,.2f} tn"
    if kind == "usd_bn":
        return f"${v:,.0f}bn"
    return f"{v:,.1f}"


def fmt_delta(d: float | None, kind: str) -> str:
    """Format a change in the same measurement kind as its reading."""
    if d is None or pd.isna(d):
        return "–"
    if kind in ("pct", "index"):
        return f"{d:+.1f} pt"
    if kind == "trillion":
        return f"{d / 1e4:+,.2f} tn"
    if kind == "usd_bn":
        return f"{d:+,.0f} bn"
    return f"{d:+,.1f}"


def fmt_level(v: float | None, kind: str) -> str:
    if v is None or pd.isna(v):
        return "–"
    if kind == "trillion":
        return fmt_trillion(v)
    if kind == "usd_bn":
        return f"${v:,.0f}bn"
    return f"{v:,.1f}"


def fmt_pts(value: float | None, digits: int = 1) -> str:
    """Difference between two percentage rates, in points."""
    if value is None or pd.isna(value):
        return "–"
    return f"{value:+.{digits}f} pt"
