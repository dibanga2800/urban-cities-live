# Variables for Azure Infrastructure

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "urban-cities-rg"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US"
}

variable "storage_account_name" {
  description = "Name of the ADLS Gen2 storage account (must be globally unique, 3-24 chars, lowercase alphanumeric)"
  type        = string
  default     = "urbancitiesadls"
}

variable "data_factory_name" {
  description = "Name of the Azure Data Factory"
  type        = string
  default     = "urban-cities-adf"
}

variable "sql_server_name" {
  description = "Name of the Azure SQL server (must be globally unique)"
  type        = string
  default     = "urban-cities-sql"
}

variable "sql_admin_username" {
  description = "Administrator username for Azure SQL"
  type        = string
  default     = "sqladmin"
  sensitive   = true
}

variable "sql_admin_password" {
  description = "Administrator password for Azure SQL"
  type        = string
  sensitive   = true
}

variable "sql_database_name" {
  description = "Name of the Azure SQL database"
  type        = string
  default     = "urban_cities_db"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "Development"
    Project     = "Urban Cities Service"
    ManagedBy   = "Terraform"
  }
}
