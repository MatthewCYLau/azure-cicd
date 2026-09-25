# Databricks notebook source
from pyspark.sql.functions import col, sum as _sum, round as _round, count

STORAGE_ACCOUNT = "st<PROJECT_CODE>data"
SILVER_PATH = (
    f"abfss://silver-cleaned@{STORAGE_ACCOUNT}.dfs.core.windows.net/risk_trades/"
)
GOLD_PATH = f"abfss://gold-aggregated@{STORAGE_ACCOUNT}.dfs.core.windows.net/daily_book_pnl_risk/"

# Read clean trades
trades_df = spark.read.format("delta").load(SILVER_PATH)

# Mock FX reference data (In real pipelines, read this from market data container)
# Converts native currency amounts to USD
trades_with_usd = (
    trades_df.withColumn(
        "fx_rate_to_usd",
        when(col("currency") == "USD", 1.0)
        .when(col("currency") == "EUR", 1.08)
        .when(col("currency") == "GBP", 1.27)
        .when(col("currency") == "JPY", 0.0067)
        .otherwise(1.0),
    )
    .withColumn("unrealized_pnl_usd", col("unrealized_pnl_ccy") * col("fx_rate_to_usd"))
    .withColumn("notional_usd", col("notional") * col("fx_rate_to_usd"))
)

# Aggregate daily risk metrics per Book / Trading Desk
gold_aggregated_df = (
    trades_with_usd.groupBy("trade_date", "book_id", "asset_class")
    .agg(
        _count("trade_id").alias("total_trades"),
        _round(_sum("notional_usd"), 2).alias("total_notional_usd"),
        _round(_sum("unrealized_pnl_usd"), 2).alias("total_unrealized_pnl_usd"),
        # Financial Risk Greeks aggregates
        _round(_sum(col("delta") * col("notional_usd")), 2).alias("net_delta_usd"),
        _round(_sum(col("vega") * col("notional_usd")), 2).alias("net_vega_usd"),
    )
    .withColumnRenamed("book_id", "desk_book")
)

# Save to Gold layer as Delta format for BI (PowerBI, Tableau) or Risk dashboards
(
    gold_aggregated_df.write.format("delta")
    .mode("overwrite")
    .partitionBy("trade_date")
    .save(GOLD_PATH)
)
