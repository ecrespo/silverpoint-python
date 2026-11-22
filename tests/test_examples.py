"""delta-001 (PY-T-16): the Databricks example notebook runs, with Databricks' globals stubbed.

The notebook is Databricks' source format: cells split on ``# COMMAND ----------``, ``# MAGIC`` cells
are not Python. ``spark.read.table("samples.nyctaxi.trips")`` is a local table with the same columns
and more rows than ``SPARK_ROW_LIMIT``, so the notebook's last cell meets the limit.
"""

import ast
import datetime as dt
import os
import shutil
from pathlib import Path

import pytest

pytest.importorskip("pyspark")
if not (os.environ.get("JAVA_HOME") or shutil.which("java")):
    pytest.skip("pyspark needs Java 17+ (JAVA_HOME or java on PATH)", allow_module_level=True)

from silverpoint import Chart

NOTEBOOK = Path(__file__).parent.parent / "examples" / "notebooks" / "databricks.py"


def cells():
    text = NOTEBOOK.read_text()
    assert text.startswith("# Databricks notebook source\n")
    return [c.strip() for c in text.split("# COMMAND ----------")]


@pytest.fixture(scope="module")
def spark():
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    session = SparkSession.builder.master("local[1]").appName("silverpoint-examples").getOrCreate()
    start = dt.datetime(2016, 2, 1)
    trips = session.range(10_050).select(
        (F.lit(start) + F.make_interval(mins=(F.col("id") * 7) % 1440)).alias("tpep_pickup_datetime"),
        ((F.col("id") % 97) / 10 + 0.5).alias("trip_distance"),
        ((F.col("id") % 89) / 2 + 3.0).alias("fare_amount"),
        (10001 + F.col("id") % 30).cast("int").alias("pickup_zip"),
    )

    class Reader:
        def table(self, name):
            assert name == "samples.nyctaxi.trips"
            return trips

    class Workspace:
        read = Reader()

    yield Workspace()
    session.stop()


def run(cell, scope):
    """Run a cell as Databricks does: the value of its last expression is the cell's output."""
    tree = ast.parse(cell)
    last = tree.body.pop() if tree.body and isinstance(tree.body[-1], ast.Expr) else None
    exec(compile(tree, str(NOTEBOOK), "exec"), scope)
    return eval(compile(ast.Expression(last.value), str(NOTEBOOK), "eval"), scope) if last else None


def test_the_databricks_notebook_runs(spark, capsys):
    shown = []
    restarted = []

    class Library:
        def restartPython(self):
            restarted.append(True)

    class DbUtils:
        library = Library()

    scope = {"spark": spark, "dbutils": DbUtils(), "displayHTML": shown.append}
    python = [c for c in cells() if not all(line.startswith("# MAGIC") for line in c.splitlines())]
    outputs = [run(cell, scope) for cell in python]

    assert restarted == [True]
    line = outputs[2]
    assert isinstance(line, Chart) and line.spec["chart"] == "line-chart"
    assert len(line.spec["data"]) == 24 and line.spec["data"][0]["hour"] == "00:00"
    assert line._repr_mimebundle_()["text/html"].startswith("<iframe ")
    assert len(shown) == 2 and all("data-sp-embed" in page for page in shown)
    assert "more than 10000 rows" in capsys.readouterr().out
