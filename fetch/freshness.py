"""Release-calendar expectations: which data month should be public by now.

Each indicator in content/indicators.yaml declares ``release_day`` - the day
of the month following the reference month by which its print is normally
out (the PMI, released on the last day of the reference month itself, uses
1). expected_latest_period() turns that into the newest period the feed
should carry today, so both fetch/run_all.py and the app can tell "the
release isn't out yet" apart from "the feed is behind".

Dependency-free on purpose: the Streamlit app imports this module, and the
app must stay runnable without the fetch requirements (akshare etc.).
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta


def release_due_date(period: str, release_day: int,
                     december_release_day: int | None = None) -> date:
    """The date by which the print for ``period`` ('YYYY-MM') should be out.

    Normally day ``release_day`` of the month after the reference month
    (clamped to the month's length). ``december_release_day`` overrides the
    December print, which publishers fold into annual press conferences:
    it counts days from January 1 of the following year and may exceed 31,
    rolling into February (MOF's full-year fiscal print has landed as late
    as Feb 1, encoded as 32).
    """
    year, month = int(period[:4]), int(period[5:7])
    if month == 12 and december_release_day is not None:
        return date(year + 1, 1, 1) + timedelta(days=december_release_day - 1)
    year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return date(year, month, min(release_day, calendar.monthrange(year, month)[1]))


def expected_latest_period(today: date, release_day: int,
                           no_january_release: bool = False,
                           december_release_day: int | None = None) -> str:
    """The newest 'YYYY-MM' period whose release should be public by today.

    ``release_day`` is calibrated to the late end of each publisher's usual
    window (July CPI, released around Aug 9-10, carries 11), so an indicator
    is only called behind once its window has fully passed.

    ``no_january_release`` marks series with no standalone January print
    (NBS activity data and customs trade publish January and February
    together in March): their expectation skips from December straight to
    the February print.
    """
    if not 1 <= release_day <= 31:
        raise ValueError(f"release_day out of range: {release_day!r}")
    if december_release_day is not None and not 1 <= december_release_day <= 62:
        raise ValueError(
            f"december_release_day out of range: {december_release_day!r}")
    year, month = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
    while release_due_date(f"{year:04d}-{month:02d}", release_day,
                           december_release_day) > today:
        year, month = (year - 1, 12) if month == 1 else (year, month - 1)
    if no_january_release and month == 1:
        year, month = year - 1, 12
    return f"{year:04d}-{month:02d}"
