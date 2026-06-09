# Running and debugging

The MCP server and the dashboard server are independent processes. Start the dashboard first, then point the MCP tool at its URL.

## Dashboard server

```
uv run varro --project-dir .
```

Options: `--host 127.0.0.1 --port 5011`. Then browse `http://127.0.0.1:5011/<name>`. Pick any free port — port-bind errors surface directly to stderr, so try another port if 5011 is taken. Port 5001 is avoided (sibling project sometimes holds it). From outside the server source tree, use the published distribution form: `uv run --with varro-mcp==<version> varro --project-dir .`.

Dashboard CSS is maintained directly in `varro/dashboard/static/dashboard.css`.

## MCP server

```
uv run varro-mcp
```

This is what MCP clients (Claude Code, Codex) ultimately invoke. The plugin's `.mcp.json` launches `bin/varro-mcp`, which resolves the plugin root and runs the published package with `uv run --with varro-mcp==<version> varro-mcp`. Set `VARRO_USE_LOCAL_SERVER=1` or `VARRO_SERVER_PROJECT=/path/to/server` to run the local server project while developing. The MCP server does not start the live dashboard server; start `varro` separately when you want to view dashboards in a browser. The snapshot tool uses dashboard URLs as state descriptors and runs outputs in-process.

## Env vars

- `VARRO_PROJECT_DIR` (default `.` for MCP tools) — project root containing `dashboards/`, `notebooks/`, `.varro/`, and `data/`
- `VARRO_PACKAGE_SPEC` (default `varro-mcp`, unpinned so published patches flow through) — package spec used by the plugin wrapper in published-package mode; set e.g. `varro-mcp==0.1.0` to pin
- `VARRO_PACKAGES_FILE` (default `{project_dir}/.varro/packages.txt`) — extra notebook package requirements passed to `uv run --with-requirements`
- `VARRO_USE_LOCAL_SERVER=1` — run `{plugin_root}/server` instead of the published package
- `VARRO_SERVER_PROJECT=/path/to/server` — run a specific local server project instead of the published package
- SQL connection config lives at `{project_dir}/.varro/sql_connection.txt`; first non-empty, non-comment line is used by the MCP `sql` tool and SQL-backed dashboards.
- Data folder convention is `{project_dir}/data`

## Taking a snapshot programmatically

```python
from pathlib import Path
from varro.dashboard.snapshot import take_snapshot

s = take_snapshot(
    "http://127.0.0.1:5011/demo?region=East",
    Path("."),
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
- **Notebook deps are workspace-specific.** The Varro Jupyter tool has the core analysis stack available. Use `install_packages` or `.varro/packages.txt` for additional project dependencies.
