import io
import tokenize
from pathlib import Path

from varro.constants import NOTEBOOKS_DIR


def resolve(name: str) -> Path:
    name = name if name.endswith(".py") else f"{name}.py"
    path = (NOTEBOOKS_DIR / name).resolve()
    if path.parent != NOTEBOOKS_DIR:
        raise RuntimeError(f"notebook must live directly inside {NOTEBOOKS_DIR}")
    return path


def _marker_lines(text: str) -> list[int]:
    lines = []
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    for tok in tokens:
        if (
            tok.type == tokenize.COMMENT
            and tok.start[1] == 0
            and tok.string.startswith("# %%")
        ):
            lines.append(tok.start[0])
    return lines


def parse_cells(text: str) -> list[str]:
    lines = text.splitlines(keepends=True)
    bounds = _marker_lines(text) + [len(lines) + 1]
    cells = []
    start = 1
    for marker in bounds:
        chunk = "".join(lines[start - 1 : marker - 1]).strip()
        if chunk:
            cells.append(chunk)
        start = marker + 1
    return cells


def append_cell(path: Path, code: str) -> None:
    with path.open("a") as f:
        f.write(f"\n# %%\n{code.rstrip()}\n")
