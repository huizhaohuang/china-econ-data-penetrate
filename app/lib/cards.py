"""Overview tiles and indicator cards.

Tiles are compact HTML (with an inline-SVG sparkline) so the overview page
stays fast once it holds fifteen-plus indicators. Indicator cards are the
explanation layer from content/indicators.yaml rendered next to each chart;
their cross-read entries become page links as soon as the target indicator
is built, and are labelled "planned" until then.
"""

from __future__ import annotations

import html
import re

import pandas as pd
import streamlit as st

from lib.charts import spark_svg
from lib.data import latest_reading
from lib.fmt import fmt_delta, fmt_level, fmt_month, fmt_value
from lib.theme import direction_color

# Where each block's page lives, relative to the app entrypoint.
BLOCK_PAGES = {
    "consumption": "views/consumption.py",
    "fiscal": "views/fiscal.py",
    "investment": "views/investment.py",
    "trade": "views/trade.py",
    "crosscutting": "views/crosscutting.py",
}


def _short_publisher(spec: dict) -> str:
    """'National Bureau of Statistics (NBS)' -> 'NBS'."""
    match = re.search(r"\(([^)]+)\)\s*$", spec.get("publisher", ""))
    return match.group(1) if match else spec.get("publisher", "")


_DELTA_LABEL = {
    "3m_avg": "vs average of last 3 published months",
    "same_month_last_year": "vs same month a year earlier",
}


def overview_tile(spec: dict, df: pd.DataFrame) -> str:
    ov = spec["metric"]["overview"]
    reading = latest_reading(df, ov)
    # A combined Jan-Feb headline may be a different measurement kind from the
    # single-month one (e.g. FAI falls back to the cumulative level).
    kind = (ov.get("combined_kind", ov["kind"]) if reading["jan_feb_combined"]
            else ov["kind"])

    value = fmt_value(reading["headline"], kind)
    unit = f"{html.escape(reading['period_label'])} · {fmt_month(reading['period'])}".strip(" ·")

    delta = reading["delta_vs_prior"]
    delta_html = ""
    if delta is not None and delta != 0:
        color = direction_color(delta, ov.get("up_is", "neutral"))
        arrow = "▲" if delta > 0 else "▼"
        delta_label = _DELTA_LABEL.get(reading["delta_mode"], _DELTA_LABEL["3m_avg"])
        delta_html = (f'<div class="tile-delta" style="color:{color}">'
                      f'{arrow} {fmt_delta(delta, kind)} {delta_label}</div>')

    # Optional secondary level line (absent for a combined Jan-Feb print).
    level_html = ""
    if ov.get("level_col") and reading["level"] is not None:
        level_html = (f'<div class="tile-foot">{fmt_level(reading["level"], ov["level_kind"])} · '
                      f'{fmt_month(reading["period"])}</div>')

    # A combined print's headline is a ytd basis, so it does not sit on the
    # single-month sparkline; don't mark a "latest" point that would mislead.
    spark_col = ov.get("spark_col", ov["col"])
    svg = spark_svg(df, spark_col, highlight=not reading["jan_feb_combined"])
    foot = f'{html.escape(_short_publisher(spec))} · {html.escape(ov.get("cadence", "monthly"))}'

    return (
        '<div class="cmp-tile">'
        f'<div class="tile-label">{html.escape(spec["name"])}</div>'
        f'<div class="tile-value">{value}<span class="tile-unit">{unit}</span></div>'
        f'{delta_html}{svg}{level_html}'
        f'<div class="tile-foot">{foot}</div>'
        "</div>"
    )


def planned_tile(name: str) -> str:
    return (
        '<div class="cmp-tile cmp-planned">'
        f'<div class="tile-label">{html.escape(name)}</div>'
        '<div class="tile-foot">planned</div>'
        "</div>"
    )


def indicator_card(spec: dict, content: dict, available: set[str]) -> None:
    """The explanation card rendered under an indicator's chart."""
    indicators = content.get("indicators", {})
    with st.container(border=True):
        st.markdown("##### About this indicator")
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown("**What it measures**")
            st.markdown(spec.get("what_it_measures", ""))
            st.markdown("**Publisher & release**")
            st.markdown(f"{spec.get('publisher', '')}. {spec.get('release', '')} "
                        f"Unit: {spec.get('unit', '')}.")
        with right:
            st.markdown("**How to read it**")
            st.markdown(spec.get("how_to_read", ""))
            if spec.get("caveats"):
                st.markdown("**Caveats**")
                st.markdown(spec["caveats"])

        cross_reads = spec.get("cross_reads", [])
        if cross_reads:
            st.markdown("**Read it with**")
            for xr in cross_reads:
                target_id = xr["id"]
                target = indicators.get(target_id)
                name = (target or {}).get("name") or xr.get("name", target_id)
                page = BLOCK_PAGES.get((target or {}).get("block"))
                if target_id in available and page:
                    st.page_link(page, label=name)
                elif target_id in available:
                    # Data exists but its block page is not built yet.
                    st.markdown(f"**{name}** · on overview")
                else:
                    st.markdown(f"**{name}** · planned")
                st.caption(xr.get("note", ""))
