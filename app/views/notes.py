"""Monthly notes page: renders content/notes/*.md, newest first.

Notes are hand-written by the owner and never auto-generated. Files are named
YYYY-MM.md (or YYYY-MM-title.md); they sort newest-first by filename.
"""

import streamlit as st

from lib import data as data_lib

st.title("Monthly notes")
st.markdown("Hand-written analysis, newest first. Each note reads the same data "
            "shown across the dashboard.")

notes = data_lib.list_notes()
if not notes:
    st.info("No notes yet. Add markdown files to content/notes/ (named "
            "YYYY-MM.md) and they appear here newest first.")
else:
    for i, note in enumerate(notes):
        if i:
            st.divider()
        st.markdown(note["body"])
