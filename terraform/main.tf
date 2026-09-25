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

resource "azurerm_databricks_workspace" "this" {
  name                = "dbw-${var.project_short_code}-prod"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "premium"

  tags = local.common_tags
}
