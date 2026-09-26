variable "resource_group_name" {
  type    = string
  default = ""
}

variable "location" {
  type    = string
  default = ""
}

variable "project" {
  default = "azure-cicd"
}

variable "project_short_code" {
  type    = string
  default = "azurecicd"
}

variable "contact" {
  default = "lau.cy.matthew@gmail.com"
}

variable "name" {
  type        = string
  description = "Name to be echo'd via Terraform null_resource command execution"
  default     = ""
}
