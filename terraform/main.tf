resource "azurerm_storage_account" "adls" {
  name                     = "st${var.project_short_code}data"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true
}

resource "azurerm_storage_container" "bronze" {
  name                  = "bronze-raw"
  storage_account_id    = azurerm_storage_account.adls.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "silver" {
  name                  = "silver-cleaned"
  storage_account_id    = azurerm_storage_account.adls.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "gold" {
  name                  = "gold-aggregated"
  storage_account_id    = azurerm_storage_account.adls.id
  container_access_type = "private"
}

resource "azurerm_databricks_workspace" "this" {
  name                = "dbw-${var.project_short_code}-prod"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "premium"

  tags = local.common_tags
}


# Get current client context
data "azurerm_client_config" "current" {}

# 1. Access Connector (Managed Identity)
resource "azurerm_databricks_access_connector" "unity" {
  name                = "ac-${var.project_short_code}-databricks"
  resource_group_name = var.resource_group_name
  location            = var.location

  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}

# 2. REQUIRED FOR UNITY CATALOG: Grant 'Reader' on Access Connector to deployment principal
resource "azurerm_role_assignment" "access_connector_reader" {
  scope                = azurerm_databricks_access_connector.unity.id
  role_definition_name = "Reader"
  principal_id         = data.azurerm_client_config.current.object_id
}

# 3. Grant 'Storage Blob Data Contributor' to the Access Connector on ADLS
resource "azurerm_role_assignment" "adls_access" {
  scope                = azurerm_storage_account.adls.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.unity.identity[0].principal_id
}

# Add a propagation delay for Azure RBAC
resource "time_sleep" "wait_rbac_propagation" {
  depends_on = [
    azurerm_role_assignment.access_connector_reader,
    azurerm_role_assignment.adls_access
  ]

  create_duration = "60s"
}
