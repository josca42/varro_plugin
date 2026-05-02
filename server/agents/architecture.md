# Architecture

MCP server giving Claude Code a data-science setup: stateful IPython + file-driven dashboards. The MCP server and the dashboard server are separate processes — the MCP server does not start, own, or depend on the dashboard. The snapshot tool takes a dashboard URL as input, so the agent picks the port and sees bind errors directly.

## Entry point

[varro/main.py](../varro/main.py) — single `FastMCP` instance named `varro`. No lifespan. Module-level initialization only:
- `_switch("sandbox")` boots a fresh IPython shell, runs `JUPYTER_INITIAL_IMPORTS`, replays `notebooks/sandbox.py`, and points `current_notebook` at it
- `exec_lock` for serializing jupyter cell execution

The dashboard server runs separately — see [dev.md](dev.md).

The `varro` CLI entrypoint [varro/cli.py](../varro/cli.py) (registered via `[project.scripts]` in [pyproject.toml](../pyproject.toml)) starts the dashboard HTTP server. The MCP server is started by MCP clients via `python -m varro.main`.

MCP tools:
- `jupyter(code, show=[...], notebook=None)` — run Python in the persistent IPython shell, optionally render named objects (DataFrames → text preview; matplotlib → PNG; plotly → PNG via `plotly.to_image`). Each successful cell is appended to the current notebook file; passing `notebook="<name>"` switches (or creates) a notebook by replaying its cells in a fresh kernel
- `sql(query, df_name=None)` — runs SQL through the shared connection-file engine via `run_sql`, optionally stores the result DataFrame in the IPython shell, and (when `df_name` is given) appends a `df_name = run_sql("""...""")` cell to the current notebook so the dataset replays on resume
- `dashboard_snapshot(url)` — given a full dashboard URL (e.g. `http://127.0.0.1:5011/sales?region=North`), runs the active page's referenced outputs, writes figures/tables/metrics/PNG under `dashboards/<name>/snapshots/<filter_key>/`

Notebook persistence detail in [notebooks.md](notebooks.md). State lives in the `.py` file; we do not pickle the live namespace.

## Dashboard subsystem ([varro/dashboard/](../varro/dashboard/))

Small modules, output-module cache by source signature, no auth, optional SQL datasets via `queries.sql` or `queries/*.sql`.

```
dashboard.md + pages/*.md  →  parser.py  →  AST  →  components.py  →  FastHTML (server.py)
queries.sql or queries/*.sql → queries.py                             →  executor.py
outputs.py or outputs/*.py →  loader.py                               →  executor.py
dashboards/index.md         →  Jinja2 markdown template                →  `/`
```

| File | Purpose |
|---|---|
| `models.py` | `@output` marker decorator, `Metric` pydantic model |
| `parser.py` | `:::` containers + `<tag />` self-closing components → AST |
| `filters.py` | `SelectFilter`, `DateRangeFilter`, `CheckboxFilter` + `resolve_select_options` (CSV or static list) |
| `loader.py` | `load_dashboard(folder, page_slug=None)` — parses overview/pages, loads optional SQL query definitions, caches output imports until `outputs.py` or `outputs/**/*.py` changes, validates output refs |
| `queries.py` | Loads named SQL datasets and executes them with dashboard filters |
| `executor.py` | Injects `filters` and matching SQL query DataFrames into output functions |
| `helpers.py` | Small FastHTML render helpers: `Figure`, `MetricCard`, `FilterInput`, `format_metric` |
| `tables.py` | Rich `<table />` support: attrs, DataFrame view, raw/display payload, Alpine controller, Styler rendering |
| `components.py` | `render_ast` — walks AST, emits FastHTML nodes for the dashboard shell. Placeholders lazy-load via HTMX |
| `server.py` | `build_app(dashboards_dir)` — creates `dashboards/index.md` if missing, serves `/`, root-level dashboard/page routes, `/_/static`, and `/{dashboard}/_/...` fragment routes |
| `snapshot.py` | `take_snapshot` — executes active-page outputs, writes per-figure PNGs (kaleido), table views, metrics |
| `../sql.py` | Shared local SQLAlchemy connection-file engine helper |

## Stack

- **FastHTML + HTMX** for server-rendered fragments and filter sync via `HX-Replace-Url` + `HX-Trigger: filtersChanged`
- **Alpine.js** for client-side tab state (no server round-trip to switch tabs)
- **Plain `dashboard.css`** served from `varro/dashboard/static/`. The dashboard frame is a shadcn/zinc design: white canvas, sticky right table of contents, compact filter bar, flat bordered cards, segmented tabs, and Inter typography.
- **Plotly** charts, rendered with `include_plotlyjs=False` (one shared CDN script)
- **Kaleido** for per-figure PNG export in snapshots

The root page `/` is editable markdown at `dashboards/index.md`. It is rendered through Jinja2 on every request; `{{ dashboards }}` expands to a markdown list of available dashboard links or `No dashboards yet.`.

## Data flow for a filter change

1. User changes a `<filter-select />` → HTMX `change delay:300ms` → `GET /{name}/_/filters?region=east` or `GET /{name}/{page}/_/filters?region=east`
2. Server replies with empty body + `HX-Replace-Url: /{name}?region=east` (or the page path) + `HX-Trigger: filtersChanged`
3. Every stable output slot (listens for `filtersChanged from:body`) re-fetches `/{name}/_/fig/...`, `/{name}/_/table/...`, `/{name}/_/metric/...` with `hx-include="#filters"` appending query params. Component attrs are carried as internal `__*` params.
4. Fragments swap inside the output slot via `hx-swap="innerHTML"` so future filter refreshes keep working.
