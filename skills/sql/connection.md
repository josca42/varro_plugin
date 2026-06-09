# SQL connection setup

The varro SQL tool reads its connection string from a single file:

```
{VARRO_PROJECT_DIR}/.varro/sql_connection.txt
```

`VARRO_PROJECT_DIR` defaults to the current working directory — i.e. the file usually lives at `.varro/sql_connection.txt`.

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

The Postgres driver (`psycopg`) ships bundled. Other drivers (e.g. `pymysql`, `duckdb-engine`) must be added separately — use `mcp__varro__install_packages` (or add them to `.varro/packages.txt`), which installs into the current environment and persists across sessions. Prefer this over editing the plugin's `pyproject.toml`, since a plugin reinstall overwrites local edits.

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

The connection file is plaintext. Add `.varro/` to `.gitignore` if the connection string contains real credentials.
