# SQL connection setup

The varro SQL tool reads its connection string from a single file:

```
{VARRO_DASHBOARDS_DIR}/.varro/sql_connection.txt
```

`VARRO_DASHBOARDS_DIR` defaults to `./dashboards` — i.e. the file usually lives at `dashboards/.varro/sql_connection.txt`.

## File format

The first non-empty, non-comment line is used as a SQLAlchemy connection URL. Comments start with `#`. Any SQLAlchemy-supported dialect works:

```
# Postgres
postgresql+psycopg://user:password@localhost:5432/dbname

# SQLite (file)
sqlite:///./local.db

# DuckDB
duckdb:///./analytics.duckdb

# MySQL
mysql+pymysql://user:password@localhost:3306/dbname
```

Driver packages (e.g. `psycopg`, `pymysql`, `duckdb-engine`) must be installed separately — add them to the plugin's `pyproject.toml` if missing.

## Engine caching

`varro.sql.get_sql_engine` caches a single engine per connection string. If the file changes between calls, the old engine is disposed and a new one is created. So you can edit `sql_connection.txt` mid-session and the next query picks it up.

## Testing the connection

Run a trivial query through the MCP tool:

```
mcp__varro__sql(query="select 1 as ok")
```

If the connection file is missing, the tool raises:

```
RuntimeError: No SQL connection file exists. Add a SQLAlchemy connection string to .../sql_connection.txt
```

Create the file (and parent `.varro/` dir if needed) and try again.

## Security note

The connection file is plaintext. Add `dashboards/.varro/` to `.gitignore` if the connection string contains real credentials.
