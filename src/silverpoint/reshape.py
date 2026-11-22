"""The host catalog's reshapes (silverpoint API delta §15.3), in Python (PY-REQ-005)."""

from __future__ import annotations

import math
from typing import Any

Row = dict[str, Any]


def _text(value: Any) -> str:
    """``String(value ?? '')`` in the library's sense, for row and column labels."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e21:
        return str(int(value))
    return str(value)


def to_matrix(
    rows: list[Row], row_column: str, column_column: str, value_column: str
) -> tuple[list[Row], str, list[str]]:
    """One output row per distinct ``row``, its values in the order columns first appear; missing cells ``None``."""
    columns: list[str] = []
    order: list[str] = []
    cells: dict[str, dict[str, Any]] = {}
    for row in rows:
        r = _text(row.get(row_column))
        c = _text(row.get(column_column))
        if r not in cells:
            cells[r] = {}
            order.append(r)
        if c not in columns:
            columns.append(c)
        cells[r][c] = row.get(value_column)
    values_key = "__values" if row_column == "values" else "values"
    data = [{row_column: r, values_key: [cells[r].get(c) for c in columns]} for r in order]
    return data, values_key, columns


def first_row_value(rows: list[Row], column: str) -> float | int | None:
    """The first row's cell as a number, or ``None`` when there is none."""
    if not rows:
        return None
    value = rows[0].get(column)
    # `Number(value)` in the library: null → 0, booleans → 0/1, blank text → 0, other text parsed.
    if value is None or isinstance(value, bool):
        number: Any = int(bool(value))
    elif isinstance(value, (int, float)):
        number = value
    else:
        text = str(value).strip()
        try:
            number = 0 if not text else None if "_" in text else float(text)
        except ValueError:
            number = None
    if number is None or (isinstance(number, float) and not math.isfinite(number)):
        return None
    return int(number) if isinstance(number, float) and number.is_integer() else number
