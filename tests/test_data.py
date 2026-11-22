"""PY-REQ-002: every input kind becomes JSON rows."""

import datetime as dt
import math

import pytest

from silverpoint.data import to_rows

EXPECTED = [{"day": "2026-11-20", "n": 1, "x": None}, {"day": "2026-11-21", "n": 2, "x": 2.5}]


def test_list_of_mappings_and_dates():
    rows = [
        {"day": dt.date(2026, 11, 20), "n": 1, "x": math.nan},
        {"day": dt.date(2026, 11, 21), "n": 2, "x": 2.5},
    ]
    assert to_rows(rows) == EXPECTED


def test_mapping_of_columns():
    assert to_rows({"day": ["2026-11-20", "2026-11-21"], "n": [1, 2], "x": [None, 2.5]}) == EXPECTED


def test_columns_and_values():
    assert to_rows({"columns": ["a", "b"], "values": [[1, 2]]}) == [{"a": 1, "b": 2}]


def test_datetime_is_iso():
    assert to_rows([{"t": dt.datetime(2026, 11, 20, 10, 30)}]) == [{"t": "2026-11-20T10:30:00"}]


def test_object_with_to_dicts():
    class Frame:
        def to_dicts(self):
            return [{"a": 1}]

    assert to_rows(Frame()) == [{"a": 1}]


def test_pandas():
    pd = pytest.importorskip("pandas")
    np = pytest.importorskip("numpy")
    df = pd.DataFrame(
        {
            "day": pd.to_datetime(["2026-11-20", "2026-11-21"]).date,
            "n": np.array([1, 2], dtype="int64"),
            "x": [np.nan, 2.5],
        }
    )
    rows = to_rows(df)
    assert rows == EXPECTED
    assert type(rows[0]["n"]) is int


def test_pandas_timestamps_and_nat():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"t": [pd.Timestamp("2026-11-20 10:30"), pd.NaT]})
    assert to_rows(df) == [{"t": "2026-11-20T10:30:00"}, {"t": None}]


def test_polars():
    pl = pytest.importorskip("polars")
    df = pl.DataFrame({"day": [dt.date(2026, 11, 20), dt.date(2026, 11, 21)], "n": [1, 2], "x": [None, 2.5]})
    assert to_rows(df) == EXPECTED


def test_pyarrow():
    pa = pytest.importorskip("pyarrow")
    table = pa.table({"day": [dt.date(2026, 11, 20), dt.date(2026, 11, 21)], "n": [1, 2], "x": [None, 2.5]})
    assert to_rows(table) == EXPECTED


def test_none_and_unknown():
    assert to_rows(None) == []
    with pytest.raises(TypeError):
        to_rows(42)


def test_no_optional_import_at_load():
    import subprocess
    import sys

    code = "import sys, silverpoint; print(sorted(m for m in ('pandas','polars','pyarrow','pyspark','flask','django','numpy') if m in sys.modules))"
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert out == "[]"


class _SparkFrame:
    """A Spark DataFrame's surface, without Spark (the bare install's CI job has no pyspark)."""

    __module__ = "pyspark.sql.connect.dataframe"

    def __init__(self, rows, arrow=False):
        self.rows, self.collected = rows, None
        if arrow:
            self.toArrow = lambda: _Table(self.rows)

    def limit(self, n):
        return _SparkFrame(self.rows[:n], arrow=hasattr(self, "toArrow"))

    def toPandas(self):
        return _Records(self.rows)

    def to_dict(self, orient):  # pandas-on-Spark and Spark both must never reach this branch
        raise AssertionError("collected the whole frame")


class _Records:
    def __init__(self, rows):
        self.rows = rows

    def to_dict(self, orient):
        return self.rows


class _Table:
    __module__ = "pyarrow.lib"

    def __init__(self, rows):
        self.rows = rows

    def to_pylist(self):
        return self.rows


class _PandasOnSpark:
    __module__ = "pyspark.pandas.frame"

    def __init__(self, rows):
        self.rows = rows

    def to_spark(self):
        return _SparkFrame(self.rows)

    def to_dict(self, orient):
        raise AssertionError("collected the whole frame")


class _Row(tuple):
    __module__ = "pyspark.sql.types"

    def asDict(self, recursive=False):
        return {"team": self[0], "wins": self[1]}


def test_spark_frames_are_read_through_limit(monkeypatch):
    """PY-REQ-002, PY-REQ-017: Spark Connect and pandas-on-Spark, Arrow or pandas, and the cap."""
    from silverpoint import data

    rows = [{"team": "A", "wins": 12}, {"team": "B", "wins": math.nan}]
    expected = [{"team": "A", "wins": 12}, {"team": "B", "wins": None}]
    assert to_rows(_SparkFrame(rows)) == expected
    assert to_rows(_SparkFrame(rows, arrow=True)) == expected
    assert to_rows(_PandasOnSpark(rows)) == expected
    monkeypatch.setattr(data, "SPARK_ROW_LIMIT", 1)
    with pytest.raises(ValueError, match="more than 1 rows"):
        to_rows(_SparkFrame(rows))


def test_spark_rows():
    assert to_rows([_Row(("A", 12))]) == [{"team": "A", "wins": 12}]
