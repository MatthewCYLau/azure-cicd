resource "databricks_notebook" "etl_script" {
  path     = "/ETL/bronze_to_silver_pipeline"
  language = "PYTHON"
  content_base64 = base64encode(<<-EOT
    # Databricks notebook source
    from pyspark.sql.functions import current_timestamp, col

    print("Running ETL pipeline step: Ingestion and Cleaning...")
    # Add PySpark transformations here
    EOT
  )
}

resource "databricks_job" "etl_workflow" {
  name = "Daily-ETL-Pipeline"

  environment {
    environment_key = "default"
    spec {
      client = "1"
    }
  }

  task {
    task_key        = "bronze_to_silver"
    environment_key = "default" # Directs this task to run on Serverless compute

    notebook_task {
      notebook_path = databricks_notebook.etl_script.path
    }
  }

  schedule {
    quartz_cron_expression = "0 0 2 * * ?" # Run daily at 02:00 AM
    timezone_id            = "UTC"
  }
}

# Notebook 0: Synthetic Raw Data Generator (Landing into Bronze)
resource "databricks_notebook" "generate_raw_data" {
  path     = "/ETL/00_generate_raw_trades"
  language = "PYTHON"
  content_base64 = base64encode(file("${path.module}/scripts/00_generate_raw_trades.py"))
}

# Notebook 1: Bronze to Silver (Cleaning & Schema Enforcement)
resource "databricks_notebook" "bronze_to_silver" {
  path     = "/ETL/01_bronze_to_silver_risk_pnl"
  language = "PYTHON"
  content_base64 = base64encode(file("${path.module}/scripts/01_bronze_to_silver.py"))
}

# Notebook 2: Silver to Gold (FX Conversion & Risk Aggregations)
resource "databricks_notebook" "silver_to_gold" {
  path     = "/ETL/02_silver_to_gold_risk_pnl"
  language = "PYTHON"
  content_base64 = base64encode(file("${path.module}/scripts/02_silver_to_gold.py"))
}
resource "databricks_job" "risk_pnl_pipeline" {
  name = "Daily-Risk-PnL-Pipeline"

  # Task 1: Generate Raw Data
  task {
    task_key = "generate_raw_trades"

    notebook_task {
      notebook_path = databricks_notebook.generate_raw_data.path
      # Pass Azure Storage Account name dynamically to the notebook
      base_parameters = {
        storage_account = azurerm_storage_account.adls.name
      }
    }
  }

  # Task 2: Bronze to Silver
  task {
    task_key = "bronze_to_silver_cleaning"

    depends_on {
      task_key = "generate_raw_trades"
    }

    notebook_task {
      notebook_path = databricks_notebook.bronze_to_silver.path
      base_parameters = {
        storage_account = azurerm_storage_account.adls.name
      }
    }
  }

  # Task 3: Silver to Gold
  task {
    task_key = "silver_to_gold_risk_aggregations"

    depends_on {
      task_key = "bronze_to_silver_cleaning"
    }

    notebook_task {
      notebook_path = databricks_notebook.silver_to_gold.path
      base_parameters = {
        storage_account = azurerm_storage_account.adls.name
      }
    }
  }

  schedule {
    quartz_cron_expression = "0 0 2 * * ?"
    timezone_id            = "UTC"
  }
}
