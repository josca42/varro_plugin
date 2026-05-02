# Design

## URL is the canonical state descriptor

`/<dashboard>?<filters>` or `/<dashboard>/<page>?<filters>` names a view, not a request. Two surfaces resolve the same URL:

- Browser (FastHTML over HTTP): what the user sees.
- `mcp__varro__dashboard_snapshot`: parses the URL and runs outputs in-process. Never fetches.

The split is intentional. Snapshot stays self-contained — port-free, server-free, agent-pickable. The dashboard HTTP server only matters for browser viewing.

## Two surfaces, two jobs

- Browser is the default for *showing* the user. Paste live URLs in replies; the user clicks, sees the same state.
- Snapshot is the default for the agent's own *reading*. Per-figure PNGs and parquet for raw data — much cheaper than full-page screenshots.

## dashboard.md is the shared index

`dashboard.md` is the user's overview page AND the agent's index of figures, tables, metrics, filters, plus the prose tying them together. Authors write it for both audiences — the narrative around the figures is what lets future sessions navigate without rerunning the analysis.

## Snapshot path mirrors URL

`dashboards/<name>/snapshots/<page>/<filter_key>/`. `_` is the sentinel for an empty segment in either axis (overview = `_`, no filters = `_`). Two pages sharing filters no longer collide.

`<filter_key>` rules: `_` for empty; otherwise sorted `key=val,key=val` with default-value filters dropped. Same encoding the URL produces.

## Stable selectors across HTMX swaps

HTMX replaces only the contents of the output slot. Identity rides on two layers so browser automation works across reloads:

- Slot (stable): `data-output-name`, `data-output-type`. Wait on this; attributes survive across reloads.
- Rendered card (replaced on each swap): `data-slot` plus repeated `data-output-name`. Target after render.

Filter wrappers carry `data-filter-name`.
