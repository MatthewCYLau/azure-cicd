# Databricks notebook source
from pyspark.sql.functions import col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, DateType

spark.sql("USE CATALOG risk_pnl")
spark.sql("USE SCHEMA portfolio")

BRONZE_VOLUME_PATH = "/Volumes/risk_pnl/portfolio/bronze_volume/trades"

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

# Read raw data using UC Volume path
raw_df = spark.read.schema(trade_schema).json(BRONZE_VOLUME_PATH)

# Clean and transform
cleaned_df = (
    raw_df.filter(col("trade_id").isNotNull() & col("book_id").isNotNull())
    .fillna({"delta": 0.0, "gamma": 0.0, "vega": 0.0, "unrealized_pnl_ccy": 0.0})
    .withColumn("ingestion_timestamp", current_timestamp())
)

# Write directly to Unity Catalog Silver Table
(
    cleaned_df.write.format("delta")
    .mode("overwrite")
    .partitionBy("trade_date")
    .saveAsTable("risk_pnl.portfolio.silver_risk_trades")
)

print(
    "Successfully created/updated Unity Catalog Table: risk_pnl.portfolio.silver_risk_trades"
)
