# Viewing a dashboard

A dashboard URL is the **canonical state descriptor**: `/<dashboard>?<filters>` or `/<dashboard>/<page>?<filters>`. The same string identifies the same view in two surfaces:

- **The browser** — where the user sees the rendered page, served by the dashboard HTTP server.
- **`mcp__varro__dashboard_snapshot`** — where the agent reads the same view offline. Outputs run in-process here; the URL is parsed but never fetched, so the dashboard server does not need to be running.

The browser is the default for *showing* the user. Snapshots are for the agent's own *reading* — much cheaper than reading a full-page screenshot, and they also dump the underlying data as parquet.

## Read first, then look

`dashboard.md` (and any `pages/*.md`) is the index. It lists what figures, tables, metrics, and filters exist, plus the prose tying them together. Read it before navigating or snapshotting.

## URL navigation

Path:
- `/<dashboard>` — overview page
- `/<dashboard>/<page>` — subpage (slug from `pages/<file>.md`, numeric prefix stripped)

Filters as query params, defaults dropped:
- `<filter-select name="region" />` → `?region=east`
- `<filter-date name="period" />` → `?period_from=2024-01-01&period_to=2024-12-31`
- `<filter-check name="active" />` → `?active=true`

Filter names and defaults are visible in the dashboard's `::: filters` block.

## Showing the user (browser)

Open the dashboard via `mcp__Claude_in_Chrome__navigate`, change the URL to encode the view you want to highlight, and paste the live URL into your reply. The user clicks; you both see the same state.

Stable selectors for browser automation:
- Each output is a stable outer **slot** (`.output-slot[data-output-name][data-output-type]`) whose contents HTMX swaps on every filter change. Wait on the slot — its attributes survive across reloads.
- Inside the slot is the **rendered card**, which is replaced on each swap. It carries `data-slot` (`varro-figure`, `varro-table`, `varro-styled-table`, or `metric-value`) and repeats `data-output-name`, so you can target the card directly once it's rendered.
- Filter wrappers carry `data-filter-name`.

The browser surface needs the dashboard HTTP server. If `http://127.0.0.1:5011/_/health` does not respond, start the server in the background before navigating:

```
uv run --project ${CLAUDE_PLUGIN_ROOT}/server varro --project-dir .
```

Default host/port is `127.0.0.1:5011`. uv auto-installs dependencies on first run.

## Reading offline (snapshot)

```
mcp__varro__dashboard_snapshot(url="http://127.0.0.1:5011/titanic/survival?sex=female")
```

The host is decorative — only the path and query are read. Snapshots write to:

```
dashboards/<name>/snapshots/<page>/<filter_key>/
  figures/<output>.png       # Plotly → kaleido PNG
  tables/<output>.parquet    # DataFrame view (columns / sort / limit applied)
  metrics.json               # all metrics for the view
  YYYY-MM-DD.date            # marker
```

`<page>` is the page slug or `_` for the overview. `<filter_key>` is `_` for no filters or sorted `key=val,key=val` with defaults dropped. Two views with the same filters but different pages no longer collide.

Read selectively after the snapshot returns:

```
Read("dashboards/titanic/snapshots/survival/sex=female/figures/curve.png")
Read("dashboards/titanic/snapshots/survival/sex=female/tables/cohort.parquet")
```

The snapshot result lists actual `figures:` and `tables:` stems — tables with attrs or duplicate names get an 8-char filename hash, so check the response rather than guessing.

## Persistent notes

`dashboards/<name>/agents/` is the per-dashboard working-memory folder (same convention as the project's CLAUDE.md / AGENTS.md). When a particular URL captures a useful view ("the female-3rd-class cohort tells the story"), add a free-form note. Future sessions read these first.

## Pitfalls

- **Tiny filtered cohorts.** Quantile bands and other binnings can fail on duplicate edges when filters narrow to a handful of rows.
- **Output name mismatch.** `<fig name="x" />` requires an `@output` named `x`. A mismatch fails at dashboard *load* with an explicit `Unknown output 'x' referenced ...` error (which lists the known outputs) — surfaced by **both** `dashboard_snapshot` and the browser (the page fails to render). The fix is to align the tag's `name=` with the `@output` function name.
- **Styler tables.** Snapshots preserve the underlying data but not the styling. Read the parquet for values; visit the browser if styling carries the message.
- **`pyarrow` is required** for parquet writes.
