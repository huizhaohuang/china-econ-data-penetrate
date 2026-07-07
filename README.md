# China Macro Panel

A public data dashboard that tracks China's economy through the lens
professional China-watchers actually use: the **GDP expenditure framework**.
Every month's data release is placed into trend context within minutes, and
every indicator is explained — what it measures, who publishes it, how to read
it, and which other indicators to read it alongside.

Built and maintained by a journalist, as both a working analytical tool and a
public, self-documenting reference. All data comes from official Chinese
publishers (NBS, MOF, PBOC, GACC); every chart credits the original agency.

## The framework

China's economy is tracked here the way an economist decomposes GDP by
expenditure — who is actually doing the spending — plus one cross-cutting layer:

| Block | Question it answers | Built indicators |
|-------|---------------------|------------------|
| **Household consumption** | How much are households spending? | Retail sales |
| **Government & fiscal** | How hard is fiscal policy pushing? | Public budget revenue |
| **Investment** | Where is capital spending going? | Fixed asset investment |
| **External trade** | Is external demand holding up? | Exports, imports, manufacturing PMI |
| **Prices, property & credit** | The deflation / credit backdrop to all four | CPI, PPI, new loans, money supply (M1/M2), total social financing |

The **Overview** page shows one sparkline tile per indicator, grouped by block,
each with the latest reading, its direction versus the last three months, and a
dateline of what updated in the past week. Each **block page** carries full
charts and an explanation card per indicator. The **Compare** view overlays two
or three indicators on a single axis (year-on-year or indexed to 100) to inspect
the linkages the cards describe. **Monthly notes** are hand-written analysis.

## Architecture

The one non-negotiable design decision: **fetching and display are strictly
separated.** Chinese official-data endpoints are unreliable from non-China IPs,
and cloud hosts (e.g. Streamlit Community Cloud) sit outside China — so the app
never touches the network at runtime.

```
akshare (official data)          run locally, with retries
        │
        ▼
   fetch/*.py  ──►  data/*.csv  +  data/*.meta.json   ──►  app/  (Streamlit)
   (one per         (committed, versioned:                 reads ONLY data/
    indicator)       the single source of truth)           and content/;
                                                            zero network calls
```

- **`fetch/`** — Python scripts using [akshare](https://github.com/akfamily/akshare),
  run locally (later optionally via GitHub Actions). Each writes one cleaned CSV
  per indicator plus a `.meta.json` sidecar (fetch time, source function, row
  count) so staleness is visible in the app. `fetch/run_all.py` runs them all
  with per-indicator error isolation.
- **`data/`** — committed CSVs, the single source of truth. Git history doubles
  as a data audit trail.
- **`app/`** — a Streamlit + Plotly app that reads only `data/` and `content/`.
  Deployable anywhere with no scraping risk.
- **`content/indicators.yaml`** — the hand-edited explanation and display layer:
  the cards, and a `metric` spec per indicator that drives its tiles and charts
  (so adding an indicator is mostly data, not code).
- **`content/notes/`** — hand-written monthly markdown notes.

## Data conventions

- All dates are first-of-month ISO strings.
- **Chinese New Year:** NBS publishes January and February combined for activity
  data. Those February rows carry only year-to-date figures and are flagged
  `jan_feb_combined`; charts show a gap by design and nothing is ever
  interpolated across it.
- Year-to-date year-on-year and single-month year-on-year are never mixed on one
  chart without a label. Series that are natively year-to-date (fiscal, FAI) are
  read that way.
- Every fetcher stores published rates as-is; year-on-year is never recomputed
  from levels, because NBS revises the prior-year base.

## Sourcing and scope

All data is official, accessed via akshare, and credited to its publisher on
every chart. Some framework indicators are **not available in the free feed**
and are shown as honest "planned" placeholders rather than approximated:
services production index, PMI sub-indices (new export orders, civil
engineering), the FAI manufacturing/infrastructure/property split, the 70-city
home-price composite, real-estate sales and development investment, budget
expenditure, and bond issuance versus quota. Commercial feeds (Mysteel, STR,
VariFlight) are deliberately out of scope.

## Run

```bash
# The app (read-only; no akshare needed)
pip install -r requirements.txt
streamlit run app/streamlit_app.py

# Refresh the data (run locally, from a China-reachable network)
pip install -r requirements-fetch.txt
python -m fetch.run_all          # all indicators
python -m fetch.retail_sales     # or one at a time
```

## Layout

```
fetch/        akshare fetchers + shared normaliser (common.py) + run_all.py
data/         one CSV + one .meta.json per indicator
app/
  streamlit_app.py   entry point and navigation
  lib/               data access, charts, tiles/cards, generic block page, theme
  views/             overview, one page per block, compare, notes
content/
  indicators.yaml    blocks, indicator cards, and per-indicator metric specs
  notes/             hand-written monthly markdown notes
```
