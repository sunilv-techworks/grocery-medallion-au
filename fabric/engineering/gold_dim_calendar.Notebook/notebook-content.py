# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "108b9665-7225-4145-8fd6-acbc0115fa73",
# META       "default_lakehouse_name": "lh_gold",
# META       "default_lakehouse_workspace_id": "5b41ba82-6075-49aa-90d8-94835e822115",
# META       "known_lakehouses": [
# META         {
# META           "id": "108b9665-7225-4145-8fd6-acbc0115fa73"
# META         }
# META       ]
# META     },
# META     "environment": {}
# META   }
# META }

# CELL ********************

"""Gold dim_calendar — generated directly, no Bronze/Silver source (DR-009).

Unlike dim_product, there's no real-world "raw" system a date dimension
comes from, so this skips Bronze/Silver entirely: config.gold_metadata
registers it with sources=[], and run_gold's dispatcher doesn't care —
it only ever reads table["gold_notebook"], so an empty sources list needs
no dispatcher change.

Mirrors packages/grocery-gen/src/grocery_gen/dimensions/calendar.py: a
plain date spine with fiscal-year/quarter (AU fiscal year runs 1 Jul -
30 Jun, named by the year it ends in) and AU national public holidays
(`holidays` package, no state subdivision — no store dimension yet to
vary by state).

Returns: row count as the notebook exit value (used by run_gold dispatcher).
"""

import holidays
from pyspark.sql.functions import (
    col,
    date_format,
    dayofmonth,
    dayofweek,
    explode,
    lit,
    month,
    pmod,
    quarter,
    sequence,
    to_date,
    weekofyear,
    when,
    year,
)

START_DATE = "2024-01-01"
END_DATE = "2026-12-31"
TARGET_TABLE = "conformed.dim_calendar"  # default lakehouse = lh_gold

dates_df = spark.createDataFrame([(1,)], ["_"]).select(
    explode(sequence(to_date(lit(START_DATE)), to_date(lit(END_DATE)))).alias("date")
)

start_year = int(START_DATE[:4])
end_year = int(END_DATE[:4])
au_holidays = holidays.country_holidays("AU", years=range(start_year, end_year + 1))
holiday_rows = [(d.isoformat(), name) for d, name in au_holidays.items()]
holidays_df = (
    spark.createDataFrame(holiday_rows, ["date_str", "holiday_name"])
    .withColumn("date", to_date(col("date_str")))
    .drop("date_str")
)

df_gold = (
    dates_df.join(holidays_df, on="date", how="left")
    .withColumn("date_key", date_format(col("date"), "yyyyMMdd").cast("int"))
    .withColumn("year", year(col("date")))
    .withColumn("quarter", quarter(col("date")))
    .withColumn("month", month(col("date")))
    .withColumn("month_name", date_format(col("date"), "MMMM"))
    .withColumn("day_of_month", dayofmonth(col("date")))
    # Spark's dayofweek is Sun=1..Sat=7; convert to ISO Mon=1..Sun=7
    .withColumn("day_of_week", pmod(dayofweek(col("date")) + lit(5), lit(7)) + lit(1))
    .withColumn("day_name", date_format(col("date"), "EEEE"))
    .withColumn("week_of_year", weekofyear(col("date")))
    .withColumn("is_weekend", col("day_of_week") >= 6)
    .withColumn(
        "fiscal_year",
        when(month(col("date")) >= 7, year(col("date")) + 1).otherwise(year(col("date"))),
    )
    .withColumn(
        "fiscal_quarter",
        (pmod(month(col("date")) - lit(7), lit(12)) / lit(3)).cast("int") + lit(1),
    )
    .withColumn("is_public_holiday", col("holiday_name").isNotNull())
)

(
    df_gold.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(TARGET_TABLE)
)

row_count = df_gold.count()
print(f"Gold dim_calendar: {row_count} rows -> lh_gold.{TARGET_TABLE}")

mssparkutils.notebook.exit(str(row_count))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
