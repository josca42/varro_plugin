---
name: jupyter
description: Use when running Python in a stateful IPython kernel via `mcp__varro__jupyter`.
---

Use `mcp__varro__jupyter` to run Python. The tool's docstring covers
selection, arguments, and result shape; this file covers usage strategy.

## Conventions

- Use `sandbox` for ad-hoc exploration. It is the default; do not pass `notebook=`.
- For substantive analysis, switch to a named notebook (e.g. `notebook="cohort_analysis"`). The notebook becomes the durable record of the analysis. After the initial switch, omit `notebook=` on subsequent calls unless you want to move to a different notebook.
- Notebook files are written to `<project>/notebooks`. `VARRO_PROJECT_DIR` overrides the project root when the MCP server is launched from elsewhere.
- Two parallel conversations using the same notebook name will clobber each other's file — use distinct names per conversation.
- Notebook names must be flat; nested paths via `notebook=` are rejected.
- For analysis that stabilises into a reusable view, refactor it into a dashboard (see the [dashboards](../dashboards/SKILL.md) skill).

## Packages

If a notebook needs a package that is not already importable, use `mcp__varro__install_packages` with package specifiers such as `["seaborn", "statsmodels>=0.14"]`. It installs into the current Varro environment for immediate use and appends the specs to `<project>/.varro/packages.txt` so the launcher includes them on future starts.

Do not run unrelated shell-level `pip install` commands for notebook dependencies unless the Varro install tool fails and you are explicitly debugging the Python environment.

## SQL inside cells

`from varro.sql import run_sql` is pre-imported, so jupyter cells can run SQL inline. Use this for **composition** — when SQL is part of a larger Python computation (queries built from Python state, multiple queries combined, query-then-transform in one cell). For single complete SQL statements, the `sql` tool is the canonical entry point — see the [sql skill](../sql/SKILL.md).

## Recovery

The notebook file is the source of truth for kernel state on replay. If a cell breaks the file, edit `<project>/notebooks/<name>.py` directly to fix or delete the offending cell, then switch back to that notebook.
