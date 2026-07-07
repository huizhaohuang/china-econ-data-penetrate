"""Chart builders. One visual grammar for the whole app:

* single-series line charts in the one accent blue, 2px, hairline solid
  gridlines, unified hover, a ringed end-marker and a direct end label;
* gaps are meaningful (NBS Jan-Feb combined publication) and are never
  bridged - connectgaps stays False everywhere;
* one y-axis per chart, always. Series on different bases (yoy vs ytd yoy
  vs level) are switched, never overlaid.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from lib.theme import (BASELINE, CATEGORICAL, DEEMPHASIS, FONT_STACK, GRID, INK,
                       INK_MUTED, INK_SECONDARY, SERIES, SURFACE)

PLOTLY_CONFIG = {"displayModeBar": False}


def compare_color(slot: int) -> str:
    """Categorical colour by a stable slot index, so colour follows the entity
    and does not repaint when the selection changes."""
    return CATEGORICAL[slot % len(CATEGORICAL)]


def compare_chart(series: list[dict], *, ticksuffix: str = "%", decimals: int = 1,
                  zero_line: bool = False, height: int = 440) -> go.Figure:
    """Overlay several series on ONE axis (never dual-axis). Each series dict:
    name, x (dates), y (values), color. A legend is always shown for 2+ series;
    end labels are added when 4 or fewer series keep them uncluttered."""
    fig = go.Figure()
    direct_label = len(series) <= 4
    for s in series:
        fig.add_trace(go.Scatter(
            x=s["x"], y=s["y"], mode="lines", name=s["name"],
            line=dict(color=s["color"], width=2), connectgaps=False,
            hovertemplate=f"%{{fullData.name}}: %{{y:.{decimals}f}}{ticksuffix}<extra></extra>",
        ))
        # Positional alignment: x may arrive as a pandas Series with a
        # non-contiguous index (gap months dropped), so label lookups would
        # place the dot at the wrong month - always align by position.
        xs = pd.Series(list(s["x"])).reset_index(drop=True)
        ys = pd.Series(list(s["y"])).reset_index(drop=True)
        last = ys.last_valid_index()
        if direct_label and last is not None:
            fig.add_trace(go.Scatter(
                x=[xs.iloc[last]], y=[ys.iloc[last]], mode="markers",
                marker=dict(color=s["color"], size=8, line=dict(color=SURFACE, width=2)),
                cliponaxis=False, hoverinfo="skip", showlegend=False,
            ))

    if zero_line:
        fig.add_hline(y=0, line_color=BASELINE, line_width=1, layer="below")
    fig.update_layout(
        height=height, margin=dict(l=8, r=16, t=16, b=8),
        plot_bgcolor=SURFACE, paper_bgcolor=SURFACE,
        font=dict(family=FONT_STACK, size=13, color=INK_SECONDARY),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=GRID,
                        font=dict(family=FONT_STACK, size=13, color=INK)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(color=INK_SECONDARY)),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=BASELINE, linewidth=1,
                     tickfont=dict(color=INK_MUTED), hoverformat="%b %Y")
    fig.update_yaxes(showgrid=True, gridcolor=GRID, gridwidth=1, zeroline=False,
                     showline=False, ticksuffix=ticksuffix, tickfont=dict(color=INK_MUTED))
    return fig


def line_chart(df: pd.DataFrame, y: str, *, ticksuffix: str = "%",
               decimals: int = 1, zero_line: bool = False,
               refline: float | None = None,
               height: int = 380) -> go.Figure:
    """Single-series line over time. `df` needs a `date` column; NaNs in
    `y` render as gaps."""
    series = df[["date", y]].copy()
    valid = series.dropna(subset=[y])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series["date"], y=series[y],
        mode="lines",
        line=dict(color=SERIES, width=2, shape="linear"),
        connectgaps=False,
        hovertemplate=f"%{{y:.{decimals}f}}{ticksuffix}<extra></extra>",
        showlegend=False,
    ))

    if valid.empty:
        # No plottable points in this slice (e.g. a YTD-only series shown on
        # the single-month view). Degrade to an empty state, never a crash.
        fig.add_annotation(
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
            text="No values published for this view and range.",
            font=dict(family=FONT_STACK, size=13, color=INK_MUTED),
        )
    else:
        last_x = valid["date"].iloc[-1]
        last_y = float(valid[y].iloc[-1])
        # End marker: ≥8px dot with a surface-colored ring so it reads on the line.
        fig.add_trace(go.Scatter(
            x=[last_x], y=[last_y],
            mode="markers",
            marker=dict(color=SERIES, size=9, line=dict(color=SURFACE, width=2)),
            cliponaxis=False,
            hoverinfo="skip",
            showlegend=False,
        ))
        fig.add_annotation(
            x=last_x, y=last_y,
            text=f"{last_y:,.{decimals}f}{ticksuffix}",
            showarrow=False, xanchor="left", xshift=10,
            font=dict(family=FONT_STACK, size=13, color=INK),
        )

    if zero_line:
        fig.add_hline(y=0, line_color=BASELINE, line_width=1, layer="below")
    if refline is not None:
        # Reference level for diffusion indices (e.g. PMI's 50 line).
        fig.add_hline(y=refline, line_color=BASELINE, line_width=1, layer="below")

    fig.update_layout(
        height=height,
        margin=dict(l=8, r=72, t=16, b=8),
        plot_bgcolor=SURFACE,
        paper_bgcolor=SURFACE,
        font=dict(family=FONT_STACK, size=13, color=INK_SECONDARY),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=GRID,
                        font=dict(family=FONT_STACK, size=13, color=INK)),
        showlegend=False,
    )
    fig.update_xaxes(
        showgrid=False, showline=True, linecolor=BASELINE, linewidth=1,
        tickfont=dict(color=INK_MUTED), hoverformat="%b %Y",
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=GRID, gridwidth=1, zeroline=False,
        showline=False, ticksuffix=ticksuffix, tickfont=dict(color=INK_MUTED),
    )
    return fig


def spark_svg(df: pd.DataFrame, value_col: str, *, highlight: bool = True,
              width: int = 150, height: int = 40) -> str:
    """Inline-SVG sparkline for overview tiles.

    Points are placed on a true calendar-month axis over the last 12 months,
    so a month with no reading (the NBS Jan-Feb gap, where January has no row
    and February carries only ytd figures) leaves a visible break instead of
    being bridged - the same never-interpolate discipline as the full charts.
    Body in the de-emphasis gray; the latest plotted point in the accent blue
    (suppressed via highlight=False when the headline is a combined print that
    does not sit on this single-month series). Hairline zero line when the
    window crosses zero.
    """
    window = df[["date", value_col]].dropna(subset=["date"]).tail(12)
    if window[value_col].notna().sum() < 2:
        return ""

    dates = pd.to_datetime(window["date"])
    ordinals = (dates.dt.year * 12 + (dates.dt.month - 1)).tolist()
    vals = window[value_col].tolist()
    o0, o1 = min(ordinals), max(ordinals)
    finite = [v for v in vals if pd.notna(v)]
    lo, hi = min(finite), max(finite)
    if hi == lo:
        hi, lo = hi + 1.0, lo - 1.0

    pad = 5.0
    x_left, x_right = 2.0, width - 8.0

    def sx(o: int) -> float:
        span = (o1 - o0) or 1
        return x_left + (x_right - x_left) * (o - o0) / span

    def sy(v: float) -> float:
        return pad + (hi - v) / (hi - lo) * (height - 2 * pad)

    parts = []
    if lo < 0 < hi:
        zy = sy(0)
        parts.append(f'<line x1="0" y1="{zy:.1f}" x2="{width}" y2="{zy:.1f}" '
                     f'stroke="{GRID}" stroke-width="1"/>')

    # Split into contiguous runs, breaking wherever a month is missing or NaN.
    runs: list[list[tuple[float, float]]] = []
    prev_o = None
    for o, v in zip(ordinals, vals):
        if pd.isna(v):
            prev_o = None
            continue
        if prev_o is None or o - prev_o != 1:
            runs.append([])
        runs[-1].append((sx(o), sy(v)))
        prev_o = o
    for run in runs:
        if len(run) == 1:
            cx, cy = run[0]
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="1.5" fill="{DEEMPHASIS}"/>')
        else:
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in run)
            parts.append(f'<polyline points="{pts}" fill="none" stroke="{DEEMPHASIS}" '
                         f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>')

    if highlight and runs:
        cx, cy = runs[-1][-1]
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3" '
                     f'fill="{SERIES}" stroke="{SURFACE}" stroke-width="1.5"/>')

    n = len(finite)
    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="last {n} monthly readings">' + "".join(parts) + "</svg>")
