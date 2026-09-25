# Databricks notebook source
from pyspark.sql.functions import col, current_timestamp, coalesce, lit, when
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    DateType,
    TimestampType,
)

# Define strict schema for raw trade landings
trade_schema = StructType(
    [
        StructField("trade_id", StringType(), False),
        StructField("book_id", StringType(), True),
        StructField("counterparty", StringType(), True),
        StructField("asset_class", StringType(), True),
        StructField("trade_date", DateType(), True),
        StructField("notional", DoubleType(), True),
        StructField("currency", StringType(), True),
        StructField("unrealized_pnl_ccy", DoubleType(), True),
        StructField("delta", DoubleType(), True),
        StructField("gamma", DoubleType(), True),
        StructField("vega", DoubleType(), True),
    ]
)

STORAGE_ACCOUNT = "st<PROJECT_CODE>data"
BRONZE_PATH = f"abfss://bronze-raw@{STORAGE_ACCOUNT}.dfs.core.windows.net/trades/"
SILVER_PATH = (
    f"abfss://silver-cleaned@{STORAGE_ACCOUNT}.dfs.core.windows.net/risk_trades/"
)

# Read raw JSON / Parquet files from Bronze
raw_df = spark.read.schema(trade_schema).json(BRONZE_PATH)

# Clean and transform
cleaned_df = (
    raw_df
    # Remove records missing critical keys
    .filter(col("trade_id").isNotNull() & col("book_id").isNotNull())
    # Fill missing sensitivities with 0.0
    .fillna({"delta": 0.0, "gamma": 0.0, "vega": 0.0, "unrealized_pnl_ccy": 0.0})
    # Add ingestion audit timestamp
    .withColumn("ingestion_timestamp", current_timestamp())
)

# Write to Silver as Delta Lake table partitioned by trade date
(
    cleaned_df.write.format("delta")
    .mode("overwrite")
    .partitionBy("trade_date")
    .save(SILVER_PATH)
)
