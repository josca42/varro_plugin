import os
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("VARRO_PROJECT_DIR", Path.cwd())).resolve()
DASHBOARDS_DIR = PROJECT_DIR / "dashboards"
NOTEBOOKS_DIR = PROJECT_DIR / "notebooks"
DATA_DIR = PROJECT_DIR / "data"
VARRO_DIR = PROJECT_DIR / ".varro"
SQL_CONNECTION_FILE = VARRO_DIR / "sql_connection.txt"
