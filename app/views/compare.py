"""Compare view: overlay two or three indicators on one axis to inspect the
linkages the indicator cards describe (e.g. exports vs imports, CPI vs PPI).

Two comparison bases, each on a single axis so nothing is dual-scaled:
  Year-on-year    - overlay the yoy series directly (like-for-like rates).
  Indexed to 100  - rebase each level series to 100 at the first shared month,
                    for series measured in different units.
"""

import pandas as pd
import streamlit as st

from lib import content as content_lib
from lib import data as data_lib
from lib.charts import PLOTLY_CONFIG, compare_chart, compare_color

st.title("Compare indicators")
st.markdown(
    "Overlay two or three indicators to inspect how they move together. "
    "Both bases share one axis - indicators on different scales are indexed to "
    "a common base rather than given a second axis."
)

content = content_lib.load_content()
available = data_lib.available_indicators()

# Stable colour slot per indicator, assigned by a fixed ordering so an
# indicator keeps its colour regardless of selection order. With more
# indicators than palette slots the preferred slot can collide inside one
# selection; the later series then takes the next free slot, so lines on one
# chart are always distinct (never a wrapped duplicate hue).
indicators = content.get("indicators", {})
all_ids = sorted(i for i in indicators if i in available and "metric" in indicators[i])
slot_of = {ind_id: i for i, ind_id in enumerate(all_ids)}
name_of = {ind_id: indicators[ind_id]["name"] for ind_id in all_ids}

N_SLOTS = 8  # size of the categorical palette


def resolve_slots(picked_ids: list[str]) -> dict[str, int]:
    used, out = set(), {}
    for ind_id in sorted(picked_ids, key=lambda i: slot_of[i]):
        s = slot_of[ind_id] % N_SLOTS
        while s in used:
            s = (s + 1) % N_SLOTS
        used.add(s)
        out[ind_id] = s
    return out

MODES = {
    "Year-on-year": {"suffix": "%", "zero": True, "field": "yoy_col",
                     "help": "Percentage change on the same month a year earlier. "
                             "Series marked (YTD) are cumulative-since-January "
                             "rates - the basis their publisher reports."},
    "Indexed to 100": {"suffix": "", "zero": False, "field": "level_col",
                       "help": "Each level series rebased to 100 at the first "
                               "month all selected series share."},
}

mode_label = st.radio("Basis", list(MODES), horizontal=True)
mode = MODES[mode_label]

# A readable default: CPI vs PPI move on comparable scales; falling back to
# the first two ids can land an unreadable pairing (e.g. CPI vs export swings).
default = [i for i in ("cpi", "ppi") if i in all_ids] or all_ids[:2]
picked = st.multiselect(
    "Indicators (pick 2 or 3)",
    options=all_ids, format_func=lambda i: name_of[i],
    default=default, max_selections=3,
)

if len(picked) < 2:
    st.info("Pick at least two indicators to compare.")
    st.stop()

frames = {}
skipped = []
for ind_id in picked:
    spec_compare = indicators[ind_id]["metric"].get("compare", {})
    col = spec_compare.get(mode["field"])
    df, _ = data_lib.load_indicator(ind_id)
    if not col or df is None or col not in df.columns:
        skipped.append(name_of[ind_id])
        continue
    s = df[["date", col]].dropna(subset=[col]).copy()
    # Never present a ytd rate as a single-month rate: label the basis.
    name = name_of[ind_id]
    if mode["field"] == "yoy_col" and spec_compare.get("yoy_is_ytd"):
        name += " (YTD)"
    frames[ind_id] = (name, s, col)

if skipped:
    st.caption(f"Not available on this basis: {', '.join(skipped)}.")

if len(frames) < 2:
    st.warning("Fewer than two of the chosen indicators support this basis. "
               "Try the other basis or different indicators.")
    st.stop()

# Indexed mode: rebase every series at the first month they all share, so
# 100 means the same date on every line.
base_date = None
if mode_label == "Indexed to 100":
    shared = None
    for _, s, col in frames.values():
        dates = set(s["date"])
        shared = dates if shared is None else shared & dates
    valid_base = None
    for d in sorted(shared or ()):
        if all(float(s.loc[s["date"] == d, col].iloc[0]) > 0
               for _, s, col in frames.values()):
            valid_base = d
            break
    if valid_base is None:
        st.warning("These series share no usable base month to index from. "
                   "Try the year-on-year basis instead.")
        st.stop()
    base_date = valid_base

slots = resolve_slots(list(frames))
series = []
for ind_id, (name, s, col) in frames.items():
    y = s[col]
    if base_date is not None:
        s = s[s["date"] >= base_date]
        y = s[col] / float(s.loc[s["date"] == base_date, col].iloc[0]) * 100.0
    series.append({"name": name, "x": s["date"], "y": y.tolist(),
                   "color": compare_color(slots[ind_id])})

st.caption(mode["help"] + (f" Base month: {base_date.strftime('%b %Y')}."
                           if base_date is not None else ""))
fig = compare_chart(series, ticksuffix=mode["suffix"], zero_line=mode["zero"])
st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)
st.caption("Source: NBS / MOF / PBOC / GACC via akshare. "
           "See each indicator's card for how the series relate.")
