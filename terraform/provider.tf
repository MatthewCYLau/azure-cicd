provider "azurerm" {
  features {}
}

# provider "databricks" {
#   host                        = "https://${azurerm_databricks_workspace.this.workspace_url}"
#   azure_workspace_resource_id = azurerm_databricks_workspace.this.id
#   auth_type                   = "azure-cli"
# }
