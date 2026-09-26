# Databricks notebook source
from pyspark.sql.functions import col, sum as _sum, round as _round, count, when

spark.sql("USE CATALOG risk_pnl")
spark.sql("USE SCHEMA portfolio")

# 1. Read directly from the Unity Catalog Silver Table
trades_df = spark.read.table("risk_pnl.portfolio.silver_risk_trades")

# 2. Convert foreign currency P&L and Notionals to USD
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

# 3. Aggregate Risk & PnL per trading book
gold_aggregated_df = (
    trades_with_usd.groupBy("trade_date", "book_id", "asset_class")
    .agg(
        count("trade_id").alias("total_trades"),
        _round(_sum("notional_usd"), 2).alias("total_notional_usd"),
        _round(_sum("unrealized_pnl_usd"), 2).alias("total_unrealized_pnl_usd"),
        _round(_sum(col("delta") * col("notional_usd")), 2).alias("net_delta_usd"),
        _round(_sum(col("vega") * col("notional_usd")), 2).alias("net_vega_usd"),
    )
    .withColumnRenamed("book_id", "desk_book")
)

# 4. Save to Unity Catalog Gold Table
(
    gold_aggregated_df.write.format("delta")
    .mode("overwrite")
    .partitionBy("trade_date")
    .saveAsTable("risk_pnl.portfolio.gold_daily_risk_pnl")
)

print(
    "Successfully created/updated Unity Catalog Table: risk_pnl.portfolio.gold_daily_risk_pnl"
)
