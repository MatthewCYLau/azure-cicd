# Retrieve latest LTS Spark runtime and single-node/multi-node instance types
data "databricks_spark_version" "latest_lts" {
  long_term_support = true
  depends_on        = [azurerm_databricks_workspace.this]
}

data "databricks_node_type" "smallest" {
  local_disk = true
  depends_on = [azurerm_databricks_workspace.this]
}

# Single-Node or Multi-Node ETL Compute Cluster
resource "databricks_cluster" "etl_cluster" {
  cluster_name            = "etl-processing-cluster"
  spark_version           = data.databricks_spark_version.latest_lts.id
  node_type_id            = "Standard_D4s_v5"
  driver_node_type_id     = "Standard_D4s_v5"
  autotermination_minutes = 30 # Terminate to reduce idle cost

  autoscale {
    min_workers = 1
    max_workers = 4
  }

  spark_conf = {
    "spark.databricks.io.cache.enabled" = "true"
  }
}

# Upload ETL Notebook to Workspace
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

# Scheduled Databricks Workflow Job
resource "databricks_job" "etl_workflow" {
  name = "Daily-ETL-Pipeline"

  job_cluster {
    job_cluster_key = "job_cluster"
    new_cluster {
      spark_version = data.databricks_spark_version.latest_lts.id
      node_type_id  = data.databricks_node_type.smallest.id
      num_workers   = 2
    }
  }

  task {
    task_key        = "bronze_to_silver"
    job_cluster_key = "job_cluster"

    notebook_task {
      notebook_path = databricks_notebook.etl_script.path
    }
  }

  schedule {
    quartz_cron_expression = "0 0 2 * * ?" # Run daily at 02:00 AM
    timezone_id            = "UTC"
  }
}
