terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
    }
    databricks = {
      source = "databricks/databricks"
    }
  }
  backend "azurerm" {
    resource_group_name  = "rg-free-dev-001"
    storage_account_name = "stmatlautfstate001"
    container_name       = "tfstate"
    key                  = "github.terraform.tfstate"
    use_oidc             = true
  }
}