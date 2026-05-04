# varro

A Codex plugin that gives the agent a small data-analysis scaffold:

- `mcp__varro__sql` — query a SQLAlchemy database, optionally store the result as a named DataFrame in a persistent kernel
- `mcp__varro__jupyter` — run Python in a stateful IPython kernel that's file-backed under `notebooks/<name>.py` (Jupytext percent format)
- `mcp__varro__dashboard_snapshot` — execute a markdown-driven dashboard's outputs and dump figures, tables, and metrics to disk

Plus three skills (`varro:dashboards`, `varro:sql`, `varro:jupyter`) that document how to use each tool and how to author dashboards.

## Why a plugin

The plugin is intentionally minimal. Treat it as a starting prompt for data-analysis work, not a finished product. Skills and code together describe the conventions; ask Codex/Claude code to grow the plugin to fit your setup — add a Python dependency, add a dashboard component, write a new SKILL.md, etc.

## Install in Codex

Requirements:

- `uv` on PATH
- Python 3.13+ available to `uv`

Add the Varro plugin marketplace:

```bash
codex plugin marketplace add josca42/varro_plugin --ref main
```

Restart Codex, open `/plugins`, select the Varro marketplace, and install **Varro**.

The plugin provides:

- Varro MCP tools for SQL, Jupyter, and dashboard snapshots
- bundled skills for dashboards, SQL, and Jupyter
- editable source code in `server/`

For development from a local clone:

```bash
git clone https://github.com/josca42/varro_plugin.git
cd varro_plugin
codex plugin marketplace add .
```

Then install or refresh **Varro** from `/plugins`. The plugin's MCP server runs via `uv run --project ./server python -m varro.main`.

## Workspace layout (the user side)

The plugin expects a workspace shaped like this:

```
your-project/
├── data/                    # files referenced by dashboards / notebooks
├── dashboards/
│   ├── .varro/
│   │   └── sql_connection.txt   # SQLAlchemy URL for mcp__varro__sql
│   └── <name>/
│       ├── dashboard.md
│       ├── outputs.py
│       └── agents/          # working-memory notes (created on demand by the agent)
└── notebooks/               # auto-created; one .py file per named notebook
```

Override paths via `VARRO_DASHBOARDS_DIR` and `VARRO_NOTEBOOKS_DIR` env vars.

## Extending the plugin

The server's working-memory notes live at [server/agents/](server/agents/index.md). Read those before changing anything in `server/varro/`.

The skills folder ([skills/](skills/)) is where progressive-loading docs live. Each skill is a directory with a brief `SKILL.md` and any number of supporting `.md` files. Add a new skill by creating `skills/<name>/SKILL.md` with a `description:` frontmatter that triggers when relevant; route to deeper `.md` files from the body when needed.
