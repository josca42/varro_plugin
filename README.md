# varro

A Claude Code plugin that gives Claude a small data-analysis scaffold:

- `mcp__varro__sql` — query a SQLAlchemy database, optionally store the result as a named DataFrame in a persistent kernel
- `mcp__varro__jupyter` — run Python in a stateful IPython kernel that's file-backed under `notebooks/<name>.py` (Jupytext percent format)
- `mcp__varro__dashboard_snapshot` — execute a markdown-driven dashboard's outputs and dump figures, tables, and metrics to disk

Plus three skills (`varro:dashboards`, `varro:sql`, `varro:jupyter`) that document how to use each tool and how to author dashboards.

## Why a plugin

The plugin is intentionally minimal. Treat it as a starting prompt for data-analysis work, not a finished product. Skills and code together describe the conventions; ask Claude Code to grow the plugin to fit your setup — add a Python dependency, add a dashboard component, write a new SKILL.md, etc.

## Install

```
claude plugin install <repo-url>
```

The plugin's MCP server runs via `uv run --project ${CLAUDE_PLUGIN_ROOT}/server python -m varro.main`, so `uv` must be on PATH.

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
│       └── agents/          # working-memory notes (created on demand by Claude)
└── notebooks/               # auto-created; one .py file per named notebook
```

Override paths via `VARRO_DASHBOARDS_DIR` and `VARRO_NOTEBOOKS_DIR` env vars.

## Extending the plugin

The server's working-memory notes live at [server/agents/](server/agents/index.md). Read those before changing anything in `server/varro/`.

The skills folder ([skills/](skills/)) is where progressive-loading docs live. Each skill is a directory with a brief `SKILL.md` and any number of supporting `.md` files. Add a new skill by creating `skills/<name>/SKILL.md` with a `description:` frontmatter that triggers when relevant; route to deeper `.md` files from the body when needed.
