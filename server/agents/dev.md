# Running and debugging

The MCP server and the dashboard server are independent processes. Start the dashboard first, then point the MCP tool at its URL.

## Dashboard server

```
uv run varro
```

Options: `--host 127.0.0.1 --port 5011 --dir dashboards`. Then browse `http://127.0.0.1:5011/<name>`. Pick any free port — port-bind errors surface directly to stderr, so try another port if 5011 is taken. Port 5001 is avoided (sibling project sometimes holds it).

Dashboard CSS is maintained directly in `varro/dashboard/static/dashboard.css`.

## MCP server

```
uv run python -m varro.main
```

This is what MCP clients (Claude Code, Codex) invoke via their config. The plugin's `.mcp.json` runs this with `--project ${CLAUDE_PLUGIN_ROOT}/server`. The MCP server does not start the dashboard — the snapshot tool takes a full URL and relies on the dashboard already running.

## Env vars

- `VARRO_DASHBOARDS_DIR` (default `./dashboards`) — where dashboard folders live on disk (used by snapshot for output paths)
- `VARRO_NOTEBOOKS_DIR` (default `./notebooks`) — where notebook `.py` files live
- SQL connection config lives at `{dashboards_dir}/.varro/sql_connection.txt`; first non-empty, non-comment line is used by the MCP `sql` tool and SQL-backed dashboards.
- Data folder convention is `{dashboards_dir}/../data` (sibling of dashboards)

## Taking a snapshot programmatically

```python
from pathlib import Path
from varro.dashboard.snapshot import take_snapshot

s = take_snapshot(
    "http://127.0.0.1:5011/demo?region=East",
    Path("dashboards"),
)
print(s)
```

The URL is a state descriptor — only path and query are read. Outputs execute in-process; the dashboard HTTP server is not consulted. Per-figure PNGs written via Kaleido.

## Known landmines

- **Route/tag names must align.** Markdown `<fig />` → route `/{dashboard}/_/fig/`. Changing one without the other yields silent 404s that only show in the browser console.
- **`pyarrow` is required** for `DataFrame.to_parquet` in snapshots.
- **Plotly-in-HTMX.** `<script>` tags inside HTMX-swapped fragments do execute because FastHTML's `fasthtml.js` extension handles them. If Plotly charts stop rendering after swap, first check that `fasthtml.js` is still being loaded in `<head>`.
- **Plain dashboard CSS.** Python render helpers emit semantic classes such as `card`, `kpi`, `filters`, `tabs-shadcn`, and `toc`. Keep CSS and helpers in sync when adding a new class.
- **Table attrs ride as `__*` params.** Dashboard filters ignore these, while table rendering and snapshots use them for columns/sort/limit/format.
- **`tab` children** render inside the same DOM as the active tab — Alpine hides inactive tabs with `x-show` + `x-cloak`. Placeholders inside hidden tabs still HTMX-load on page load; they're just not visible.
- **Markdown rendering is client-side** via `MarkdownJS` + `HighlightJS` ([server.py](../varro/dashboard/server.py)). The server emits raw markdown inside `<div class="marked">`; `marked.js` rewrites it to HTML on page load. HTMX swaps do not re-run marked — the markdown blocks in `dashboard.md` are only rendered once on initial page load, which is fine because the shell layout is static.
- **Tiny filtered cohorts.** Some dashboards narrow to a handful of rows; derived quantile bands must tolerate duplicate bin edges.
- **Notebook deps are intentionally small.** The Varro Jupyter tool has pandas/numpy/plotly/matplotlib available, but not `sklearn`; use dependency-free analysis unless adding modeling dependencies intentionally.
