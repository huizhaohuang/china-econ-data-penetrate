"""Generic block page: renders every indicator in a block from its
``metric`` spec in content/indicators.yaml, so one code path serves all five
blocks. Each indicator gets a view selector, a chart, a sourced caption, a data
table and its explanation card.
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from lib import content as content_lib
from lib import data as data_lib
from lib import freshness as freshness_lib
from lib.cards import indicator_card
from lib.charts import PLOTLY_CONFIG, line_chart
from lib.fmt import fmt_day, fmt_month

RANGES = {"5 years": 5, "10 years": 10, "All": None}


def _range_slice(df: pd.DataFrame, years: int | None) -> pd.DataFrame:
    if years is None:
        return df
    cutoff = df["date"].max() - pd.DateOffset(years=years)
    return df[df["date"] >= cutoff]


def _render_indicator(ind_id: str, spec: dict, content: dict, available: set) -> None:
    df, meta = data_lib.load_indicator(ind_id)
    if df is None:
        return
    views = spec["metric"]["views"]

    st.divider()
    st.subheader(spec["name"])

    # One filter row above the chart it scopes.
    fcol1, fcol2 = st.columns([3, 2])
    view_label = fcol1.radio("View", [v["label"] for v in views], horizontal=True,
                             key=f"{ind_id}-view")
    range_label = fcol2.radio("Range", list(RANGES), horizontal=True,
                              key=f"{ind_id}-range")
    view = next(v for v in views if v["label"] == view_label)

    dfv = _range_slice(df, RANGES[range_label])
    plot_col = view["col"]
    if view.get("scale"):
        dfv = dfv.assign(_plot=dfv[view["col"]] / view["scale"])
        plot_col = "_plot"
    fig = line_chart(dfv, plot_col, ticksuffix=view.get("suffix", "%"),
                     decimals=view.get("decimals", 1), zero_line=view.get("zero", False),
                     refline=view.get("refline"))

    # "Data through" tracks the plotted series, not the frame, so a Jan-Feb
    # combined newest row does not overstate how current the single-month line is.
    plotted = df.dropna(subset=[view["col"]])
    through = fmt_month(plotted["date"].iloc[-1]) if not plotted.empty else "n/a"

    # A print the release calendar says is public but the data lacks gets a
    # notice - and the cause matters: a feed lagging its publisher and a
    # panel nobody refreshed look identical in the data but need different
    # fixes, so the copy must not blame the feed for a stale fetch.
    status = freshness_lib.currency_status(spec, meta)
    stale_note = ""
    if status and status["behind"]:
        reason = ("the source feed is behind the release calendar"
                  if status["cause"] == "feed"
                  else "the panel's data refresh is overdue")
        stale_note = f' · Awaiting {fmt_month(status["expected"])} — {reason}'

    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)
    st.markdown(
        f'<div class="cmp-source">{html.escape(spec.get("source_line", ""))} · '
        f'Data through {through} · '
        f'Fetched {fmt_day(data_lib.fetched_at(meta))}{stale_note}</div>',
        unsafe_allow_html=True,
    )
    if view.get("note"):
        st.caption(view["note"])

    with st.expander("Data table"):
        table = df.sort_values("date", ascending=False)
        st.dataframe(
            table, hide_index=True, width="stretch",
            column_config={"date": st.column_config.DatetimeColumn("Month", format="MMM YYYY")},
        )

    indicator_card(spec, content, available)


def render_block(block_id: str) -> None:
    content = content_lib.load_content()
    available = data_lib.available_indicators()
    block = content["blocks"][block_id]

    st.title(block["title"])
    st.markdown(block.get("description", ""))

    built = [(i, s) for i, s in content_lib.indicators_in_block(content, block_id)
             if i in available and "metric" in s]
    if not built:
        st.info("Indicators for this block are not built yet.")
    for ind_id, spec in built:
        _render_indicator(ind_id, spec, content, available)

    planned = block.get("planned", [])
    if planned:
        st.divider()
        st.caption("Planned for this block: " + "; ".join(planned) + ".")
