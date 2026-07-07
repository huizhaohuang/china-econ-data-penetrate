"""Overview page: the whole framework at a glance.

One tile per built indicator, grouped into the five blocks, plus muted
placeholders for planned indicators - so the page always shows the full
shape of the tracking framework, not just what is fetched so far.
"""

import streamlit as st

from lib import content as content_lib
from lib import data as data_lib
from lib.cards import BLOCK_PAGES, overview_tile, planned_tile
from lib.fmt import fmt_month

st.title("China Macro Panel")
st.markdown(
    "Tracking China's economy through the GDP expenditure framework — "
    "household consumption, government & fiscal, investment and external "
    "trade — plus the prices, property and credit layer that cuts across "
    "all four."
)

content = content_lib.load_content()
available = data_lib.available_indicators()

# Dateline: which indicators were refreshed in the past week. Only carded
# indicators appear - an orphan CSV without a yaml entry stays out of copy.
fresh = []
for ind_id in sorted(available):
    spec = content.get("indicators", {}).get(ind_id)
    if not spec:
        continue
    df, meta = data_lib.load_indicator(ind_id)
    days = data_lib.days_since_fetch(meta)
    if df is not None and days is not None and days <= 7:
        fresh.append(f"{spec['name']} "
                     f"(data through {fmt_month(df['date'].iloc[-1])})")
if fresh:
    st.caption("Updated in the past 7 days: " + "; ".join(fresh) + ".")
else:
    st.caption("No indicator updates in the past 7 days.")

for block_id, block in content_lib.ordered_blocks(content):
    st.divider()
    st.subheader(block["title"])
    st.caption(block.get("description", ""))

    tiles = []
    for ind_id, spec in content_lib.indicators_in_block(content, block_id):
        # A half-added indicator (CSV but no metric spec yet) is omitted
        # rather than crashing the front page.
        if ind_id in available and "metric" in spec:
            df, _ = data_lib.load_indicator(ind_id)
            tiles.append(overview_tile(spec, df))
    tiles.extend(planned_tile(name) for name in block.get("planned", []))

    cols = st.columns(3)
    for i, tile in enumerate(tiles):
        with cols[i % 3]:
            st.markdown(tile, unsafe_allow_html=True)

    if block_id in BLOCK_PAGES:
        st.page_link(BLOCK_PAGES[block_id], label=f"Open {block['title'].lower()} →")
