---
name: sql
description: Use when querying the project's SQL database via `mcp__varro__sql`.
---

Use `mcp__varro__sql` to query the database. The tool's docstring covers
selection, arguments, and result shape; this file covers usage strategy.

## When to reach for `connection.md`

If the connection isn't configured yet, or you get a `No SQL connection file exists` error, see [connection.md](connection.md).

## Patterns

- Always preview with a small `LIMIT` before running aggregates over millions of rows. The MCP response truncates output but the kernel still holds the full DataFrame.
- For dashboard-backed queries, prefer `queries.sql` (named SQL datasets in the dashboard folder) over inline SQL — see the dashboards skill, [authoring.md](../dashboards/authoring.md).
- The kernel pre-imports `from varro.sql import run_sql`, so inside `mcp__varro__jupyter` cells you can call `df = run_sql("...")` directly without going through the SQL tool. The SQL tool is the right entry when you want the call recorded for replay; inline `run_sql` inside a jupyter cell is for transient computation.
- A `Warning: query returned 0 rows.` line in the response is a hint to inspect WHERE clauses or filter values.
