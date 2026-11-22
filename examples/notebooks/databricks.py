# Databricks notebook source
# MAGIC %md
# MAGIC # silverpoint in Databricks
# MAGIC
# MAGIC Charts from Spark tables. Import this file into a workspace (**Workspace → Import → File**, or a
# MAGIC Git folder), attach it to any compute, serverless included, and run it. It reads
# MAGIC `samples.nyctaxi.trips`, which every workspace has.
# MAGIC
# MAGIC - A Spark DataFrame goes straight into a builder; at most `silverpoint.data.SPARK_ROW_LIMIT`
# MAGIC   (10,000) rows are read, through `limit`, so aggregate in Spark first.
# MAGIC - A chart as a cell's value draws itself in a sandboxed frame; `displayHTML(chart.to_html(render="client"))`
# MAGIC   draws one more anywhere in a cell.
# MAGIC - Each chart carries its own copy of the script (about 0.5 MB): a cell's output may be 10 MB by
# MAGIC   default on Runtime 17+, and a notebook keeps about fifteen charts before Databricks stops
# MAGIC   saving revision snapshots (10 MB).

# COMMAND ----------

# MAGIC %pip install silverpoint

# COMMAND ----------

dbutils.library.restartPython()  # noqa: F821 - a Databricks global

# COMMAND ----------

from pyspark.sql import functions as F  # noqa: E402 - after the restart cell, as Databricks needs

import silverpoint  # noqa: E402

trips = spark.read.table("samples.nyctaxi.trips")  # noqa: F821 - a Databricks global

by_hour = (
    trips.groupBy(F.hour("tpep_pickup_datetime").alias("hour"))
    .agg(F.count("*").alias("trips"), F.round(F.avg("fare_amount"), 2).alias("fare"))
    .orderBy("hour")
    .withColumn("hour", F.format_string("%02d:00", "hour"))
)

silverpoint.line_chart(
    by_hour, x="hour", value="trips", secondary="fare", title="Trips per pickup hour", curve="monotone"
)

# COMMAND ----------

# Several charts in one cell: displayHTML draws each where it is called.
by_zip = (
    trips.groupBy(F.col("pickup_zip").cast("string").alias("zip"))
    .agg(F.count("*").alias("trips"))
    .orderBy(F.desc("trips"))
    .limit(12)
)
distance = (
    trips.select("trip_distance", "fare_amount").where("trip_distance > 0 AND fare_amount > 0").limit(2_000)
)

displayHTML(  # noqa: F821 - a Databricks global
    silverpoint.bar_chart(
        by_zip, x="zip", value="trips", orientation="rows", title="Busiest pickup ZIPs"
    ).to_html(render="client")
)
displayHTML(  # noqa: F821 - a Databricks global
    silverpoint.scatter_chart(distance, x="trip_distance", y="fare_amount", title="Fare by distance").to_html(
        render="client"
    )
)

# COMMAND ----------

# The whole table is more than a chart reads: the error says so before anything is collected.
try:
    silverpoint.scatter_chart(trips, x="trip_distance", y="fare_amount")
except ValueError as error:
    print(error)
