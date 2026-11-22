"""PY-REQ-002, PY-REQ-017 (delta-001): Spark tables, read against a local Spark session."""

import datetime as dt
import os
import shutil

import pytest

pyspark = pytest.importorskip("pyspark")
if not (os.environ.get("JAVA_HOME") or shutil.which("java")):
    pytest.skip("pyspark needs Java 17+ (JAVA_HOME or java on PATH)", allow_module_level=True)

import silverpoint  # noqa: E402
from silverpoint import data  # noqa: E402
from silverpoint.data import to_rows  # noqa: E402


@pytest.fixture(scope="module")
def spark():
    from pyspark.sql import SparkSession

    session = SparkSession.builder.master("local[1]").appName("silverpoint-tests").getOrCreate()
    yield session
    session.stop()


def test_spark_dataframe(spark):
    df = spark.createDataFrame(
        [("A", 12, dt.date(2026, 11, 20)), ("B", None, dt.date(2026, 11, 21))], ["team", "wins", "day"]
    )
    assert to_rows(df) == [
        {"team": "A", "wins": 12, "day": "2026-11-20"},
        {"team": "B", "wins": None, "day": "2026-11-21"},
    ]


def test_a_list_of_rows(spark):
    rows = spark.createDataFrame([("A", 12)], ["team", "wins"]).collect()
    assert to_rows(rows) == [{"team": "A", "wins": 12}]


def test_a_builder_takes_the_dataframe(spark):
    df = spark.createDataFrame([("A", 12), ("B", 9)], ["team", "wins"])
    chart = silverpoint.bar_chart(df, x="team", value="wins")
    assert chart.spec["data"] == [{"team": "A", "wins": 12}, {"team": "B", "wins": 9}]


def test_more_rows_than_the_limit_is_refused_before_collecting_them(spark, monkeypatch):
    monkeypatch.setattr(data, "SPARK_ROW_LIMIT", 5)
    with pytest.raises(ValueError, match=r"more than 5 rows.*groupBy"):
        to_rows(spark.range(50))
    assert len(to_rows(spark.range(5))) == 5
