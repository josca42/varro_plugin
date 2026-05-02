---
name: sql
description: Use when querying the project's SQL database. Calls `mcp__varro__sql` with a SQLAlchemy-style query string. Connection lives at `dashboards/.varro/sql_connection.txt`. Pass `df_name` to keep the result in the kernel namespace and have the call appended to the current notebook for replay.
---

Use `mcp__varro__sql` to query the database.

## Quick reference

```
mcp__varro__sql(query="select * from sales where region = 'east' limit 100")
mcp__varro__sql(query="select region, sum(amount) as revenue from sales group by 1", df_name="region_revenue")
```

- The result is a pandas DataFrame. The tool returns a preview with row count and dtypes; full data lives in the kernel.
- `df_name` is required if you want to keep the result for downstream analysis. Without it, the call is exploratory and the DataFrame is not stored.
- When `df_name` is given, the call is appended to the current notebook (`notebooks/<name>.py`) as `df_name = run_sql("""...""")` so the dataset reappears on notebook replay.
- Date columns are auto-converted to pandas Timestamp (any column with dtype `date`, `datetime`, or `Timestamp`).

## When to reach for `connection.md`

If the connection isn't configured yet, or you get a `No SQL connection file exists` error, see [connection.md](connection.md).

## Patterns

- Always preview with a small `LIMIT` before running aggregates over millions of rows. The MCP response truncates output but the kernel still holds the full DataFrame.
- For dashboard-backed queries, prefer `queries.sql` (named SQL datasets in the dashboard folder) over inline SQL — see the dashboards skill, [authoring.md](../dashboards/authoring.md).
- The kernel pre-imports `from varro.sql import run_sql`, so inside `mcp__varro__jupyter` cells you can call `df = run_sql("...")` directly without going through the SQL tool. The SQL tool is the right entry when you want the call recorded for replay; inline `run_sql` inside a jupyter cell is for transient computation.
- Empty result sets surface as `Warning: query returned 0 rows.` in the response — treat that as a hint to inspect WHERE clauses or filter values.
