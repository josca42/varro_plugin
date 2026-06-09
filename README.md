# Varro

**Obsidian for data analysis** — a small Codex / Claude code plugin that wraps the everyday data tasks in good defaults and lets the agent grow them to fit your project.

## Thesis

Inspired by answer.ai and pi: Uses fasthtml, htmx and various code snippet from answer.ai repos. Is intented to be a small, opinionated core that codex/claude code can change to fit your needs. The plugin ships a scaffold:

- a stateful Python kernel,
- a SQL tool wired to your database,
- a markdown → dashboard rendering surface,

— and nothing more. Components, CSS, helpers, even the tools themselves are editable in place. When you need something different, ask the agent to change it. Skills and code together describe the conventions; the plugin is a starting prompt, not a finished product.

## Install

Probably easiest installed in Codex Desktop by using the marketplace git repo
https://github.com/josca42/varro_marketplace.git.

Before first use, run the runtime setup in [INSTALL.md](INSTALL.md). Varro needs
`uv` on `PATH`, and `uv` needs access to Python 3.13+.

## Stack

- **FastHTML + HTMX** — server-rendered dashboard fragments, filter swaps without full page reloads
- **Alpine.js** for client-side tab state
- **Plotly** charts, **Kaleido** for PNG export in snapshots
- Plain [`dashboard.css`](server/varro/dashboard/static/dashboard.css) — change a token, restyle the whole thing

## Four tools

- **`mcp__varro__sql`** — query a SQLAlchemy database, optionally store the result as a named DataFrame in the persistent kernel
- **`mcp__varro__jupyter`** — run Python in a stateful IPython kernel, file-backed as `notebooks/<name>.py` (Jupytext percent format)
- **`mcp__varro__dashboard_snapshot`** — take a dashboard URL, run its outputs, and dump figures, tables, and metrics to disk so the agent can read them without screenshots
- **`mcp__varro__install_packages`** — install Python packages into the current Varro environment and persist them in `.varro/packages.txt`

Plus four skills (`varro:dashboards`, `varro:sql`, `varro:jupyter`, `varro:workflow`) that document how to use each tool and how to author dashboards.

## Markdown → dashboard

Dashboards are markdown, extended with the Docusaurus admonition syntax (`:::`) for layout and self-closing component tags for content:

```md
:::filters
<filter-select name="region" options="data:sales.csv:region" default="all" />
:::

:::grid cols=2
<metric name="total_revenue" />
<fig name="revenue_by_month" />
:::
```

Each `<fig />` / `<table />` / `<metric />` dispatches to an `@output`-decorated Python function in `outputs.py`. The return type chooses the renderer — `Metric`, `pd.DataFrame`, `Styler`, or Plotly figure.

The dashboard URL (e.g. `/<name>?region=east`) is the canonical state descriptor: the same string drives the live browser view and the offline `dashboard_snapshot` tool.

Authoring reference: [skills/dashboards/authoring.md](skills/dashboards/authoring.md).

## Install in Codex

Requirements:

- `uv` on PATH
- Python 3.13+ available to `uv`

Add the Varro plugin marketplace:

```bash
codex plugin marketplace add josca42/varro_marketplace --ref main
```

Restart Codex, open `/plugins`, select the Varro marketplace, and install **Varro**.

The plugin provides:

- Varro MCP tools for SQL, Jupyter, and dashboard snapshots
- bundled skills for dashboards, SQL, and Jupyter
- a `bin/varro-mcp` launcher that runs the published `varro-mcp` Python distribution through `uv`

For development from a local clone:

```bash
git clone https://github.com/josca42/varro_plugin.git
cd varro_plugin
codex plugin marketplace add .
```

Then install or refresh **Varro** from `/plugins`. The plugin's MCP server runs through `bin/varro-mcp`, which resolves the installed plugin root and then runs `uv run --with varro-mcp==<version> varro-mcp`. The dashboard command is shipped by the same distribution, so it can be started with `uv run --with varro-mcp==<version> varro --project-dir .`. For local development before publishing, set `VARRO_USE_LOCAL_SERVER=1` or `VARRO_SERVER_PROJECT=/path/to/server` to run the bundled server project instead.

The local marketplace entry points at `plugins/varro`, a symlink back to the repo root. That keeps Codex's installer happy even if your checkout directory is named something other than `varro`.

## Workspace layout (the user side)

The plugin expects a workspace shaped like this:

```
your-project/
├── .varro/
│   ├── sql_connection.txt   # SQLAlchemy URL for mcp__varro__sql
│   └── packages.txt         # optional extra Python packages for Jupyter
├── data/                    # files referenced by dashboards / notebooks
├── dashboards/
│   └── <name>/
│       ├── dashboard.md
│       ├── outputs.py
│       └── agents/          # working-memory notes (created on demand by the agent)
└── notebooks/
    └── <name>.py            # auto-created named notebooks
```

The project root defaults to the current working directory for MCP tools. Set `VARRO_PROJECT_DIR` if the server is launched from elsewhere.

Add notebook dependencies either by editing `.varro/packages.txt` with one package spec per line or by using `mcp__varro__install_packages`. The launcher passes that file to `uv run --with-requirements`, so package additions persist across Codex threads.

## Extending the plugin

The server's working-memory notes live at [server/agents/](server/agents/index.md). Read those before changing anything in `server/varro/`.

The skills folder ([skills/](skills/)) is where progressive-loading docs live. Each skill is a directory with a brief `SKILL.md` and any number of supporting `.md` files. Add a new skill by creating `skills/<name>/SKILL.md` with a `description:` frontmatter that triggers when relevant; route to deeper `.md` files from the body when needed.
