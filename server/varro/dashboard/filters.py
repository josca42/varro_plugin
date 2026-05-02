from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Mapping

import pandas as pd
from pydantic import BaseModel, ConfigDict, field_validator

SelectOption = tuple[str, str]


class Filter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    name: str
    label: str | None = None

    @field_validator("label", mode="before")
    @classmethod
    def _default_label(cls, value: str | None, info) -> str | None:
        if value is None or value == "":
            return info.data.get("name") or None
        return value

    def parse_query_params(self, params: Mapping[str, str]) -> dict[str, Any]:
        raise NotImplementedError

    def url_params(self, values: Mapping[str, Any]) -> dict[str, str]:
        raise NotImplementedError


class SelectFilter(Filter):
    type: Literal["select"] = "select"
    default: str = "all"
    options_spec: str = ""

    def parse_query_params(self, params: Mapping[str, str]) -> dict[str, Any]:
        return {self.name: params.get(self.name, self.default)}

    def url_params(self, values: Mapping[str, Any]) -> dict[str, str]:
        v = values.get(self.name, self.default)
        return {self.name: str(v)} if v != self.default else {}


class DateRangeFilter(Filter):
    type: Literal["daterange"] = "daterange"
    default_from: str | None = None
    default_to: str | None = None

    def parse_query_params(self, params: Mapping[str, str]) -> dict[str, Any]:
        fk, tk = f"{self.name}_from", f"{self.name}_to"
        return {
            fk: params.get(fk) or self.default_from,
            tk: params.get(tk) or self.default_to,
        }

    def url_params(self, values: Mapping[str, Any]) -> dict[str, str]:
        fk, tk = f"{self.name}_from", f"{self.name}_to"
        out: dict[str, str] = {}
        if (fv := values.get(fk)) and fv != self.default_from:
            out[fk] = str(fv)
        if (tv := values.get(tk)) and tv != self.default_to:
            out[tk] = str(tv)
        return out


class CheckboxFilter(Filter):
    type: Literal["checkbox"] = "checkbox"
    default: bool = False

    @field_validator("default", mode="before")
    @classmethod
    def _parse_default(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.lower() == "true"
        return bool(v)

    def parse_query_params(self, params: Mapping[str, str]) -> dict[str, Any]:
        v = params.get(self.name)
        if v is None:
            return {self.name: self.default}
        return {self.name: v.lower() == "true"}

    def url_params(self, values: Mapping[str, Any]) -> dict[str, str]:
        v = values.get(self.name, self.default)
        return {self.name: "true" if v else "false"} if v != self.default else {}


def filter_from_component(type_: str, attrs: dict[str, str]) -> Filter | None:
    name = attrs.get("name", "")
    if not name:
        return None
    label = attrs.get("label")

    if type_ == "filter-select":
        return SelectFilter(
            name=name,
            label=label,
            default=attrs.get("default", "all"),
            options_spec=attrs.get("options", ""),
        )
    if type_ == "filter-date":
        return DateRangeFilter(
            name=name,
            label=label,
            default_from=attrs.get("default_from"),
            default_to=attrs.get("default_to"),
        )
    if type_ == "filter-check":
        return CheckboxFilter(
            name=name,
            label=label,
            default=attrs.get("default", "false"),
        )
    return None


def resolve_select_options(spec: str, root: Path) -> list[SelectOption]:
    spec = spec.strip()
    if not spec:
        return []

    if spec.startswith("data:"):
        rest = spec[len("data:"):]
        path_part, _, col = rest.rpartition(":")
        if not path_part or not col:
            raise ValueError(
                f"Bad select options spec {spec!r}: expected data:<path>:<column>"
            )
        file_path = root / "data" / path_part
        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(file_path)
        elif suffix in (".parquet", ".pq"):
            df = pd.read_parquet(file_path)
        elif suffix == ".json":
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported data file type: {suffix}")
        values = sorted(df[col].astype(str).unique().tolist())
        return [("all", "All")] + [(value, value) for value in values]

    values = [s.strip() for s in spec.split(",") if s.strip()]
    return [(value, "All" if value == "all" else value) for value in values]
