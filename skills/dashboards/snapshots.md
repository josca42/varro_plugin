# Snapshots

Use `mcp__varro__dashboard_snapshot` to execute a dashboard's outputs and dump the rendered figures, tables, and metrics to disk. Useful for verifying changes look right and for inspecting dashboard state without opening a browser.

## Prerequisite

The dashboard server must already be running at the URL you snapshot. The MCP server does not start it. From the plugin's server directory:

```
uv run --project ${CLAUDE_PLUGIN_ROOT}/server varro --dir dashboards
```

(Or whatever local equivalent is configured in your workspace.) Default host/port is `127.0.0.1:5011`.

## Calling the tool

Pass a full URL, including any filters as query params:

```
mcp__varro__dashboard_snapshot(url="http://127.0.0.1:5011/titanic?sex=female&pclass=3")
```

The active page's referenced outputs run, and results are written under:

```
dashboards/<name>/snapshots/<filter_key>/
  YYYY-MM-DD.date          # empty marker file
  figures/<output>.png     # kaleido-rendered per-figure PNG
  tables/<output>.parquet
  metrics.json
```

`filter_key` rules:
- `_` when no filters are set
- `key1=val1,key2=val2` sorted alphabetically when filters are set
- Default values are dropped from the key (so `region=all` does not appear if the default is `all`)

## Inspecting snapshots

Read PNGs and parquet files directly from disk to inspect what rendered:

```
Read("dashboards/<name>/snapshots/<filter_key>/figures/<output>.png")
Read("dashboards/<name>/snapshots/<filter_key>/tables/<output>.parquet")
Read("dashboards/<name>/snapshots/<filter_key>/metrics.json")
```

The PNG is what the user would see on the dashboard. The parquet is the underlying data — useful for checking outliers, missing values, or whether a filter narrowed the cohort to too few rows.

## Common pitfalls

- **Tiny filtered cohorts.** If the filters narrow the dashboard to a handful of rows, derived quantile bands and other binnings can fail on duplicate edges. Snapshot a representative filter combination after non-trivial filter changes.
- **Route/tag name mismatch is silent.** Markdown `<fig name="x" />` requires an `@output` function named `x` whose return type implies a figure. A mismatch surfaces as a 404 in the browser console, not as a snapshot error. Run the dashboard in a browser at least once after structural changes.
- **`pyarrow` is required** for `DataFrame.to_parquet` in snapshots.
