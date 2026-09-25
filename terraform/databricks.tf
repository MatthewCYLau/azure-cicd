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
