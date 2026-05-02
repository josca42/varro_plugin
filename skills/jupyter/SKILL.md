---
name: jupyter
description: Use when running Python in a stateful IPython kernel via `mcp__varro__jupyter`.
---

Use `mcp__varro__jupyter` to run Python. The tool's docstring covers
selection, arguments, and result shape; this file covers usage strategy.

## Conventions

- Use `sandbox` for ad-hoc exploration. It is the default; do not pass `notebook=`.
- For substantive analysis, switch to a named notebook (e.g. `notebook="cohort_analysis"`). The notebook becomes the durable record of the analysis. After the initial switch, omit `notebook=` on subsequent calls — passing it again re-switches and resets the kernel.
- Two parallel conversations using the same notebook name will clobber each other's file — use distinct names per conversation.
- `notebooks/` must be a flat directory; nested paths via `notebook=` are rejected.
- For analysis that stabilises into a reusable view, refactor it into a dashboard (see the [dashboards](../dashboards/SKILL.md) skill).

## SQL inside cells

The kernel has `from varro.sql import run_sql` pre-imported, so you can query inline:

```python
df = run_sql("select * from sales limit 100")
```

Use this for transient queries inside an analysis. Use `mcp__varro__sql` with `df_name=...` when you want the query recorded as a top-level cell that replays on notebook resume.

## Recovery

The notebook file is the source of truth for kernel state on replay. If a cell breaks the file, edit `notebooks/<name>.py` directly to fix or delete the offending cell, then switch back to that notebook.
