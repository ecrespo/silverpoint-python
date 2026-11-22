"""A chart, its data, roles, options and appearance → a validated ``ChartSpec`` dict (PY-REQ-001,
PY-REQ-004, PY-REQ-005). Binds and does not query: the same rules as the library's ``specFromTable``."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ._catalog import charts, host_catalog, options_of, snake
from ._closest import closest, did_you_mean
from .data import Row, cell, columns_of, to_rows
from .errors import SpecError
from .reshape import first_row_value, to_matrix

APPEARANCE = ("ground", "substrate", "mode", "palette")


def _quoted(names: Sequence[str]) -> str:
    return ", ".join(f'"{n}"' for n in names)


def chart_entry(slug: str) -> dict[str, Any]:
    known = charts()
    if slug not in known:
        raise SpecError(
            "chart",
            f'Unknown chart "{slug}".{did_you_mean(slug, list(known))}',
            chart=slug,
            suggestions=closest(slug, list(known)),
        )
    return known[slug]


def _check_options(slug: str, entry: dict[str, Any], options: Mapping[str, Any]) -> dict[str, Any]:
    """Options keyed by the library's (camel-case) names, each known and within its ``values``."""
    declared = {o["name"]: o for o in options_of(entry)}
    by_snake = {snake(name): name for name in declared}
    out: dict[str, Any] = {}
    unknown: list[str] = []
    for key, value in options.items():
        name = key if key in declared else by_snake.get(key)
        if name is None:
            unknown.append(key)
            continue
        option = declared[name]
        if value is not None and "values" in option and value not in option["values"]:
            raise SpecError(
                "value",
                f'{slug}: "{value}" is not a value of `{name}`; its values are {_quoted(option["values"])}.'
                f"{did_you_mean(str(value), option['values'])}",
                option=name,
                value=value,
                values=list(option["values"]),
            )
        if value is not None:
            out[name] = cell(value)
    if unknown:
        hints = "".join(did_you_mean(u, list(declared) + list(by_snake)) for u in unknown)
        raise SpecError("prop", f"{slug} has no option {_quoted(unknown)}.{hints}", props=unknown)
    return out


def _check_appearance(appearance: Mapping[str, Any]) -> dict[str, Any]:
    catalog = host_catalog()["appearance"]
    allowed = {
        "ground": [g["name"] for g in catalog["grounds"]],
        "substrate": list(dict.fromkeys(s["name"] for g in catalog["grounds"] for s in g["substrates"])),
        "mode": [m["name"] for m in catalog["modes"]],
        "palette": [p["name"] for p in catalog["palettes"]],
    }
    out: dict[str, Any] = {}
    for key in APPEARANCE:
        value = appearance.get(key)
        if value is None:
            continue
        if value not in allowed[key]:
            raise SpecError(
                "value",
                f'"{value}" is not a {key}; the {key}s are {_quoted(allowed[key])}.'
                f"{did_you_mean(str(value), allowed[key])}",
                option=key,
                value=value,
                values=allowed[key],
            )
        out[key] = value
    return out


def _check_size(width: Any, height: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in (("width", width), ("height", height)):
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise SpecError(
                "size", f"`{key}` must be a positive number of pixels, not {value!r}.", **{key: value}
            )
        out[key] = value
    return out


def build_spec(
    chart: str,
    data: Any = None,
    *,
    roles: Mapping[str, str | Sequence[str]] | None = None,
    options: Mapping[str, Any] | None = None,
    appearance: Mapping[str, Any] | None = None,
    width: Any = None,
    height: Any = None,
    id: str | None = None,
) -> dict[str, Any]:
    entry = chart_entry(chart)
    roles = dict(roles or {})
    props = _check_options(chart, entry, options or {})
    look = _check_appearance(appearance or {})
    size = _check_size(width, height)
    spec_data: list[Row] | None = None

    if entry["binding"] == "none":
        if roles or data is not None:
            raise SpecError(
                "shape",
                f"{chart} is not fed from a table: {entry.get('reason') or 'it has no binding'}. "
                "Give its props as options.",
            )
    else:
        rows = to_rows(data)
        if isinstance(data, Mapping) and "columns" in data:
            names = list(data["columns"])
            repeated = [c for i, c in enumerate(names) if names.index(c) != i]
            if repeated:
                raise SpecError("shape", f"The table repeats a column name: {_quoted(repeated)}.")
        columns = columns_of(rows, data)
        known = [r["id"] for r in entry["roles"]]
        strange = [r for r in roles if r not in known]
        if strange:
            raise SpecError(
                "shape",
                f"{chart} has no role {_quoted(strange)}; its roles are {_quoted(known)}."
                f"{''.join(did_you_mean(s, known) for s in strange)}",
            )
        mapped: dict[str, list[str]] = {}
        for role in entry["roles"]:
            given = roles.get(role["id"])
            if given is None or (not isinstance(given, str) and len(given) == 0):
                continue
            mapped[role["id"]] = [given] if isinstance(given, str) else list(given)
        missing = [r["id"] for r in entry["roles"] if r["required"] and r["id"] not in mapped]
        used = list(dict.fromkeys(c for cs in mapped.values() for c in cs))
        unknown_columns = [c for c in used if c not in columns]
        if missing or unknown_columns:
            parts = []
            if missing:
                parts.append(f"{chart} needs the role {_quoted(missing)}")
            for c in unknown_columns:
                parts.append(f'the data has no column "{c}"{did_you_mean(c, columns)}')
            raise SpecError(
                "role",
                "; ".join(parts) + f". Columns: {_quoted(columns)}.",
                missing=missing,
                unknownColumns=unknown_columns,
            )
        table = [{name: row.get(name) for name in used} for row in rows]
        reshape = entry.get("reshape")
        if reshape == "matrix":
            row_c, col_c, val_c = (mapped[i][0] for i in ("row", "column", "value"))
            spec_data, values_key, labels = to_matrix(table, row_c, col_c, val_c)
            props.update({"labelKey": row_c, "valuesKey": values_key, "columnLabels": labels})
        elif reshape == "first-row":
            role = entry["roles"][0]
            value = first_row_value(table, mapped[role["id"]][0])
            if value is None:
                raise SpecError(
                    "shape",
                    f"{chart} draws one value from the table's first row, and the table has no number there.",
                )
            props[role["id"]] = value
        else:
            spec_data = table
            for role in entry["roles"]:
                cols = mapped.get(role["id"])
                if not cols or role["prop"] is None:
                    continue
                props[role["prop"]] = cols if role["multiple"] else cols[0]

    spec: dict[str, Any] = {"chart": chart}
    if spec_data is not None:
        spec["data"] = spec_data
    if props or entry["binding"] != "none":
        spec["props"] = props
    spec.update(look)
    spec.update(size)
    if id is not None:
        spec["id"] = id
    return spec
