# Databricks notebook source
import random
from datetime import date, timedelta
from pyspark.sql import SparkSession

# Set Unity Catalog context
spark.sql("USE CATALOG risk_pnl")
spark.sql("USE SCHEMA portfolio")

# Create a UC Volume mapped to Bronze external location if it doesn't exist
spark.sql("""
    CREATE EXTERNAL VOLUME IF NOT EXISTS risk_pnl.portfolio.bronze_volume
    LOCATION 'abfss://bronze-raw@stazurecicddata.dfs.core.windows.net/'
""")

BRONZE_VOLUME_PATH = "/Volumes/risk_pnl/portfolio/bronze_volume/trades"

currencies = ["USD", "EUR", "GBP", "JPY"]
books = ["EQ_DERIV_NY", "FX_FLOW_LDN", "RATES_DESK_TYO", "CREDIT_HY_NY"]
asset_classes = ["Equity", "FX", "Rates", "Credit"]
counterparties = ["CP_GOLDMAN", "CP_JPMORGAN", "CP_BARCLAYS", "CP_CITI"]

data = []
base_date = date.today()

for i in range(1, 501):
    trade_date = (base_date - timedelta(days=random.randint(0, 5))).strftime("%Y-%m-%d")
    currency = random.choice(currencies)

    trade = {
        "trade_id": f"TRD-{10000 + i}",
        "book_id": random.choice(books),
        "counterparty": random.choice(counterparties),
        "asset_class": random.choice(asset_classes),
        "trade_date": trade_date,
        "notional": float(round(random.uniform(100000, 10000000), 2)),
        "currency": currency,
        "unrealized_pnl_ccy": float(round(random.uniform(-50000, 150000), 2)),
        "delta": float(round(random.uniform(-0.9, 0.9), 4)),
        "gamma": float(round(random.uniform(0.0, 0.1), 4)),
        "vega": float(round(random.uniform(-1000, 5000), 2)),
    }
    data.append(trade)

df = spark.createDataFrame(data)

# Write to Unity Catalog Volume
(df.write.format("json").mode("overwrite").save(BRONZE_VOLUME_PATH))

print(
    f"Successfully wrote {df.count()} raw trades to Unity Catalog Volume: {BRONZE_VOLUME_PATH}"
)
