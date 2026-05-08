import re
from pathlib import Path

from varro.constants import NOTEBOOKS_DIR

_CELL_RE = re.compile(r"^# %%.*$", re.MULTILINE)


def resolve(name: str) -> Path:
    name = name if name.endswith(".py") else f"{name}.py"
    path = (NOTEBOOKS_DIR / name).resolve()
    if path.parent != NOTEBOOKS_DIR:
        raise RuntimeError(f"notebook must live directly inside {NOTEBOOKS_DIR}")
    return path


def parse_cells(text: str) -> list[str]:
    return [c.strip() for c in _CELL_RE.split(text) if c.strip()]


def append_cell(path: Path, code: str) -> None:
    with path.open("a") as f:
        f.write(f"\n# %%\n{code.rstrip()}\n")
