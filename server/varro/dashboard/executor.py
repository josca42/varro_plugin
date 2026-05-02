from __future__ import annotations

import inspect
from typing import Any

from sqlalchemy.engine import Engine

from varro.dashboard.loader import Dashboard
from varro.dashboard.queries import execute_query


def output_query_names(dash: Dashboard, output_name: str) -> set[str]:
    if output_name not in dash.outputs:
        raise KeyError(f"Unknown output {output_name!r} in dashboard {dash.name!r}")
    return {
        name
        for name in inspect.signature(dash.outputs[output_name]).parameters
        if name in dash.queries
    }


def execute_output(
    dash: Dashboard,
    output_name: str,
    filters: dict[str, Any],
    engine: Engine | None = None,
) -> Any:
    if output_name not in dash.outputs:
        raise KeyError(f"Unknown output {output_name!r} in dashboard {dash.name!r}")

    fn = dash.outputs[output_name]
    kwargs: dict[str, Any] = {}

    for param_name in inspect.signature(fn).parameters:
        if param_name == "filters":
            kwargs[param_name] = filters
            continue

        if param_name in dash.queries:
            if engine is None:
                raise RuntimeError(
                    f"Output {output_name!r} requires SQL query {param_name!r}, "
                    "but no SQL connection is configured."
                )
            kwargs[param_name] = execute_query(
                dash.queries[param_name],
                filters,
                engine,
            )
            continue

        known_queries = ", ".join(sorted(dash.queries)) or "none"
        raise TypeError(
            f"Unknown parameter {param_name!r} on output {output_name!r}. "
            f"Use 'filters' or one of the dashboard query names: {known_queries}."
        )

    return fn(**kwargs)
