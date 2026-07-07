"""Design tokens and page-level CSS.

One muted palette across the whole app: a single accent blue for data series,
grays for chrome, and red/green reserved exclusively for direction (better /
worse), never for decoration. Values mirror .streamlit/config.toml.
"""

import streamlit as st

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BORDER = "rgba(11,11,11,0.10)"

SERIES = "#2a78d6"        # the one accent hue; every single-series chart uses it
DEEMPHASIS = "#c3c2b7"    # context lines, sparkline body

# Categorical slots for the compare view only, in the dataviz-validated order
# (worst adjacent CVD dE 24.2). Colour follows the entity, never its rank -
# see compare_color(). Single-series charts never use these; they use SERIES.
CATEGORICAL = ["#2a78d6", "#1baf7a", "#eda100", "#008300",
               "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"]

GOOD = "#006300"          # direction only: reading moved the welcome way
BAD = "#d03b3b"           # direction only: reading moved the unwelcome way

FONT_STACK = 'system-ui, -apple-system, "Segoe UI", sans-serif'

_CSS = f"""
<style>
.cmp-tile {{
  border: 1px solid {BORDER};
  border-radius: 8px;
  padding: 14px 16px 12px 16px;
  background: {SURFACE};
  margin-bottom: 12px;
}}
.cmp-tile .tile-label {{ font-size: 0.82rem; color: {INK_SECONDARY}; margin-bottom: 2px; }}
.cmp-tile .tile-value {{ font-size: 1.65rem; font-weight: 600; color: {INK}; line-height: 1.15; }}
.cmp-tile .tile-unit  {{ font-size: 0.78rem; font-weight: 400; color: {INK_MUTED}; margin-left: 2px; }}
.cmp-tile .tile-delta {{ font-size: 0.78rem; margin-top: 2px; }}
.cmp-tile .tile-foot  {{ font-size: 0.74rem; color: {INK_MUTED}; margin-top: 6px; }}
.cmp-tile.cmp-planned {{ border-style: dashed; background: transparent; }}
.cmp-tile.cmp-planned .tile-label {{ color: {INK_MUTED}; }}
.cmp-source {{ font-size: 0.78rem; color: {INK_MUTED}; margin-top: -6px; }}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def direction_color(delta: float | None, up_is: str) -> str:
    """Map a change to a text color. Red/green only ever mean direction."""
    if delta is None or delta == 0 or up_is == "neutral":
        return INK_SECONDARY
    improving = (delta > 0) == (up_is == "good")
    return GOOD if improving else BAD
