# Main Terraform configuration for Azure resources
# This file creates ADLS Gen2, Azure Data Factory, and PostgreSQL Server

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    http = {
      source  = "hashicorp/http"
      version = "~> 3.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
  required_version = ">= 1.0.0"
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
  
  # Subscription ID (optional - will use az cli default if not specified)
  subscription_id = "12f0f306-0cdf-41a6-9028-a7757690a1e2"
  
  # Skip automatic resource provider registration to avoid conflicts
  skip_provider_registration = true
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = var.tags
}

# Storage Account for ADLS Gen2
resource "azurerm_storage_account" "adls" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true # Enables hierarchical namespace for ADLS Gen2

  tags = var.tags
}

# Storage Container for data lake
resource "azurerm_storage_data_lake_gen2_filesystem" "raw" {
  name               = "raw"
  storage_account_id = azurerm_storage_account.adls.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "processed" {
  name               = "processed"
  storage_account_id = azurerm_storage_account.adls.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "curated" {
  name               = "curated"
  storage_account_id = azurerm_storage_account.adls.id
}

# Azure Data Factory
resource "azurerm_data_factory" "main" {
  name                = var.data_factory_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# Grant Data Factory access to Storage Account
resource "azurerm_role_assignment" "adf_storage_blob_contributor" {
  scope                = azurerm_storage_account.adls.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.main.identity[0].principal_id
}

# Grant Service Principal access to Storage Account (for Airflow ETL tasks)
resource "azurerm_role_assignment" "sp_storage_blob_contributor" {
  scope                = azurerm_storage_account.adls.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = "9306b861-8960-496a-9a0d-3f996df4a7fb"  # Service Principal object_id
}

# Azure SQL Server
resource "azurerm_mssql_server" "main" {
  name                         = var.sql_server_name
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  version                      = "12.0"
  administrator_login          = var.sql_admin_username
  administrator_login_password = var.sql_admin_password
  minimum_tls_version          = "1.2"

  tags = var.tags
}

# Azure SQL Database
resource "azurerm_mssql_database" "main" {
  name         = var.sql_database_name
  server_id    = azurerm_mssql_server.main.id
  collation    = "SQL_Latin1_General_CP1_CI_AS"
  license_type = "LicenseIncluded"
  sku_name     = "Basic"
  
  tags = var.tags
}

# Firewall rule to allow Azure services
resource "azurerm_mssql_firewall_rule" "allow_azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# Get current public IP automatically
data "http" "current_ip" {
  url = "https://api.ipify.org"
}

# Firewall rule to allow your current IP
resource "azurerm_mssql_firewall_rule" "allow_current_ip" {
  name             = "AllowCurrentIP"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = data.http.current_ip.response_body
  end_ip_address   = data.http.current_ip.response_body
}

# Grant Service Principal access to Data Factory (for pipeline creation)
data "azurerm_client_config" "current" {}

resource "azurerm_role_assignment" "sp_data_factory_contributor" {
  scope                = azurerm_data_factory.main.id
  role_definition_name = "Data Factory Contributor"
  principal_id         = "9306b861-8960-496a-9a0d-3f996df4a7fb"  # Service Principal object_id
}

# Create SQL table using local-exec provisioner
resource "null_resource" "create_sql_table" {
  depends_on = [
    azurerm_mssql_database.main,
    azurerm_mssql_firewall_rule.allow_current_ip
  ]

  triggers = {
    database_id = azurerm_mssql_database.main.id
  }

  provisioner "local-exec" {
    command     = "cd '${path.module}/../notebook'; python create_sql_table.py"
    interpreter = ["PowerShell", "-Command"]
    on_failure  = continue  # Allow manual execution if provisioner fails
  }
}

# Create ADF pipeline using local-exec provisioner
resource "null_resource" "create_adf_pipeline" {
  depends_on = [
    azurerm_data_factory.main,
    azurerm_storage_account.adls,
    azurerm_mssql_database.main,
    azurerm_role_assignment.sp_data_factory_contributor,
    null_resource.create_sql_table
  ]

  triggers = {
    adf_id = azurerm_data_factory.main.id
  }

  provisioner "local-exec" {
    command     = "cd '${path.module}/../notebook'; python create_adf_pipeline.py"
    interpreter = ["PowerShell", "-Command"]
    on_failure  = continue  # Allow manual execution if provisioner fails
  }
}
