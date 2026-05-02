from __future__ import annotations

from types import ModuleType
from typing import Callable, Literal

from pydantic import BaseModel


class Metric(BaseModel):
    value: float | int
    label: str
    format: Literal["number", "currency", "percent"] = "number"
    change: float | None = None
    change_label: str | None = None


def output(fn: Callable) -> Callable:
    fn._is_output = True  # type: ignore[attr-defined]
    return fn


def get_outputs(module: ModuleType) -> dict[str, Callable]:
    return {
        name: obj
        for name, obj in vars(module).items()
        if callable(obj)
        and getattr(obj, "_is_output", False)
        and getattr(obj, "__module__", None) == module.__name__
    }
