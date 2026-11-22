"""Tabular input → JSON rows (PY-REQ-002). pandas, polars, pyarrow and pyspark are detected, never imported."""

from __future__ import annotations

import datetime as dt
import math
from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import Any

Row = dict[str, Any]


def cell(value: Any) -> Any:
    """One cell as JSON: dates as ISO strings, NaN/NaT as ``None``, numpy scalars as Python numbers."""
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return None if math.isnan(value) else value
    if isinstance(value, Decimal):
        return None if value.is_nan() else float(value)
    if isinstance(value, dt.datetime):
        if type(value).__name__ == "NaTType":
            return None
        return value.isoformat()
    if isinstance(value, (dt.date, dt.time)):
        return value.isoformat()
    kind = type(value).__name__
    if kind in ("NaTType", "NAType"):
        return None
    if kind in ("Timestamp", "datetime64"):
        text = str(value)
        return None if text == "NaT" else value.isoformat() if hasattr(value, "isoformat") else text
    item = getattr(value, "item", None)
    if callable(item) and type(value).__module__ == "numpy":
        return cell(item())
    if isinstance(value, Mapping):
        return {str(k): cell(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [cell(v) for v in value]
    if callable(item):
        return cell(item())
    return value


def _rows_from_columns(columns: Mapping[str, Iterable[Any]]) -> list[Row]:
    names = list(columns)
    series = [list(columns[n]) for n in names]
    length = max((len(s) for s in series), default=0)
    return [
        {n: cell(s[i] if i < len(s) else None) for n, s in zip(names, series, strict=True)}
        for i in range(length)
    ]


SPARK_ROW_LIMIT = 10_000
"""The most rows read from a Spark or pandas-on-Spark DataFrame (PY-REQ-017, delta-001)."""


def _from_spark(frame: Any) -> list[Row]:
    """At most ``SPARK_ROW_LIMIT`` rows, through ``limit`` so that a large table never reaches the driver."""
    limit = SPARK_ROW_LIMIT
    head = frame.limit(limit + 1)
    rows = to_rows(head.toArrow() if hasattr(head, "toArrow") else head.toPandas())
    if len(rows) > limit:
        raise ValueError(
            f"The Spark DataFrame has more than {limit} rows; a chart reads at most "
            f"silverpoint.data.SPARK_ROW_LIMIT. Aggregate it in Spark first (groupBy(...).agg(...)) "
            "or take what the chart needs with .limit(n)."
        )
    return rows


def to_rows(data: Any) -> list[Row]:
    """Rows from a list of mappings, a mapping of columns, ``{"columns", "values"}``, a pandas or
    polars DataFrame, a pyarrow Table, or any object with ``to_dict("records")`` or ``to_dicts()``."""
    if data is None:
        return []
    module = type(data).__module__.split(".")[0]
    if module == "pyspark":
        if hasattr(data, "to_spark"):  # pandas-on-Spark
            return _from_spark(data.to_spark())
        if hasattr(data, "limit") and (hasattr(data, "toArrow") or hasattr(data, "toPandas")):
            return _from_spark(data)
    if module == "pandas" and hasattr(data, "to_dict"):
        frame = data
        if hasattr(frame, "reset_index") and getattr(frame.index, "name", None) is not None:
            frame = frame.reset_index()
        return [{str(k): cell(v) for k, v in r.items()} for r in frame.to_dict("records")]
    if module == "pyarrow" and hasattr(data, "to_pylist"):
        return [{str(k): cell(v) for k, v in r.items()} for r in data.to_pylist()]
    if hasattr(data, "to_dicts"):
        return [{str(k): cell(v) for k, v in r.items()} for r in data.to_dicts()]
    if hasattr(data, "to_dict") and not isinstance(data, Mapping):
        return [{str(k): cell(v) for k, v in r.items()} for r in data.to_dict("records")]
    if isinstance(data, Mapping):
        if set(data) == {"columns", "values"}:
            columns = list(data["columns"])
            return [{c: cell(v) for c, v in zip(columns, values, strict=False)} for values in data["values"]]
        if set(data) == {"rows"}:
            return to_rows(data["rows"])
        return _rows_from_columns(data)
    if isinstance(data, (list, tuple)):
        if data and all(hasattr(r, "asDict") for r in data):  # Spark Rows, from DataFrame.collect()
            return [{str(k): cell(v) for k, v in r.asDict(recursive=True).items()} for r in data]
        if all(isinstance(r, Mapping) for r in data):
            return [{str(k): cell(v) for k, v in r.items()} for r in data]
        raise TypeError("A list of rows must hold mappings (one dict per row).")
    raise TypeError(
        f"Cannot read {type(data).__name__} as a table: pass rows, a mapping of columns, "
        "a pandas, polars or Spark DataFrame, or a pyarrow Table."
    )


def columns_of(rows: list[Row], given: Any = None) -> list[str]:
    """Column names in first-seen order (or the declared ``columns`` of a column-form table)."""
    if isinstance(given, Mapping) and "columns" in given:
        return list(given["columns"])
    seen: list[str] = []
    for row in rows:
        for key in row:
            if key not in seen:
                seen.append(key)
    return seen
