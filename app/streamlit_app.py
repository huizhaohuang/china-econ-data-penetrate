"""App entrypoint. Run from the repo root:

    streamlit run app/streamlit_app.py

The app reads only the committed CSVs in data/ and the hand-edited content
in content/ - no network calls at runtime.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from lib.theme import inject_css

st.set_page_config(
    page_title="China Macro Panel",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

nav = st.navigation({
    "": [st.Page("views/overview.py", title="Overview", default=True)],
    "Blocks": [
        st.Page("views/consumption.py", title="Household consumption"),
        st.Page("views/fiscal.py", title="Government & fiscal"),
        st.Page("views/investment.py", title="Investment"),
        st.Page("views/trade.py", title="External trade"),
        st.Page("views/crosscutting.py", title="Prices, property & credit"),
    ],
    "Tools": [
        st.Page("views/compare.py", title="Compare indicators"),
        st.Page("views/notes.py", title="Monthly notes"),
    ],
})

with st.sidebar:
    st.caption(
        "Official Chinese data, fetched locally via akshare and committed "
        "as versioned CSVs. The app itself makes no network calls. "
        "Each chart credits the original publishing agency."
    )

nav.run()
