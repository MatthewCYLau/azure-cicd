# Databricks notebook source
import json
import random
from datetime import date, timedelta
from pyspark.sql import SparkSession

STORAGE_ACCOUNT = "st<PROJECT_CODE>data"
BRONZE_PATH = f"abfss://bronze-raw@{STORAGE_ACCOUNT}.dfs.core.windows.net/trades/"

# 1. Generate realistic synthetic trade data
currencies = ["USD", "EUR", "GBP", "JPY"]
books = ["EQ_DERIV_NY", "FX_FLOW_LDN", "RATES_DESK_TYO", "CREDIT_HY_NY"]
asset_classes = ["Equity", "FX", "Rates", "Credit"]
counterparties = ["CP_GOLDMAN", "CP_JPMORGAN", "CP_BARCLAYS", "CP_CITI"]

data = []
base_date = date.today()

for i in range(1, 501):  # Generate 500 mock trades
    trade_date = (base_date - timedelta(days=random.randint(0, 5))).strftime("%Y-%m-%d")
    currency = random.choice(currencies)

    trade = {
        "trade_id": f"TRD-{10000 + i}",
        "book_id": random.choice(books),
        "counterparty": random.choice(counterparties),
        "asset_class": random.choice(asset_classes),
        "trade_date": trade_date,
        "notional": round(random.uniform(100000, 10000000), 2),
        "currency": currency,
        "unrealized_pnl_ccy": round(random.uniform(-50000, 150000), 2),
        "delta": round(random.uniform(-0.9, 0.9), 4),
        "gamma": round(random.uniform(0.0, 0.1), 4),
        "vega": round(random.uniform(-1000, 5000), 2),
    }
    data.append(trade)

# 2. Convert to PySpark DataFrame and write to ADLS Bronze as JSON
df = spark.read.json(sc.parallelize([json.dumps(d) for d in data]))

(df.write.format("json").mode("overwrite").save(BRONZE_PATH))

print(f"Successfully wrote {df.count()} raw trades to {BRONZE_PATH}")
