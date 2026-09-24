resource "azurerm_container_registry" "this" {
  name                = "cr${var.project_short_code}${terraform.workspace}001"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Basic"
  tags                = local.common_tags
}