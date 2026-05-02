import pandas as pd
import io
import math
from pathlib import Path
from PIL import Image

SNAPSHOT_MAX_PIXELS = 1_500_000


def df_preview(
    df: pd.DataFrame,
    max_rows: int = 10,
    name: str = "df",
    max_cell_chars: int = 40,
) -> str:
    """Generate a pipe-separated DataFrame preview."""
    if df.index.name:
        df = df.reset_index()
    n_rows = min(max_rows, len(df))
    preview = df.head(n_rows).map(
        lambda v: v[: max_cell_chars - 1] + "…"
        if isinstance(v, str) and len(v) > max_cell_chars
        else v
    )
    csv_string = preview.to_csv(
        sep="|",
        index=False,
        float_format="%.3f",
        na_rep="N/A",
    )
    return f"{name}.head({n_rows})\n" + csv_string


def df_dtype_map(df: pd.DataFrame) -> dict[str, str]:
    dtype_map = {}
    for col, dtype in df.dtypes.items():
        # FIXME: Check if dtype == "object" is correct
        if dtype == "object" and len(df) > 0:
            sample = df[col].dropna().iloc[0] if df[col].notna().any() else None
            type_name = type(sample).__name__ if sample is not None else "object"
        else:
            type_name = str(dtype)
        dtype_map[col] = type_name
    return dtype_map


def df_dtypes(df: pd.DataFrame) -> str:
    parts = [f"{col}={type_name}" for col, type_name in df_dtype_map(df).items()]
    return "dtypes: " + ", ".join(parts)


def optimize_png_bytes(png_bytes: bytes, *, max_pixels: int) -> bytes:
    with Image.open(io.BytesIO(png_bytes)) as image:
        width, height = image.size
        area = width * height
        if area > max_pixels:
            scale = math.sqrt(max_pixels / area)
            width = max(1, int(width * scale))
            height = max(1, int(height * scale))
            image = image.resize((width, height), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        image.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
