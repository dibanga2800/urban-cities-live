# Output values for created resources

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "storage_account_name" {
  description = "Name of the ADLS Gen2 storage account"
  value       = azurerm_storage_account.adls.name
}

output "storage_account_primary_endpoint" {
  description = "Primary DFS endpoint of the storage account"
  value       = azurerm_storage_account.adls.primary_dfs_endpoint
}

output "storage_account_primary_access_key" {
  description = "Primary access key for the storage account"
  value       = azurerm_storage_account.adls.primary_access_key
  sensitive   = true
}

output "data_factory_name" {
  description = "Name of the Azure Data Factory"
  value       = azurerm_data_factory.main.name
}

output "data_factory_id" {
  description = "ID of the Azure Data Factory"
  value       = azurerm_data_factory.main.id
}

output "sql_server_fqdn" {
  description = "Fully qualified domain name of the Azure SQL server"
  value       = azurerm_mssql_server.main.fully_qualified_domain_name
}

output "sql_database_name" {
  description = "Name of the Azure SQL database"
  value       = azurerm_mssql_database.main.name
}

output "sql_connection_string" {
  description = "Connection string for Azure SQL (without password)"
  value       = "Server=tcp:${azurerm_mssql_server.main.fully_qualified_domain_name},1433;Initial Catalog=${var.sql_database_name};Persist Security Info=False;User ID=${var.sql_admin_username};Password=PASSWORD;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"
  sensitive   = true
}

output "adls_filesystems" {
  description = "List of created ADLS Gen2 filesystems"
  value = [
    azurerm_storage_data_lake_gen2_filesystem.raw.name,
    azurerm_storage_data_lake_gen2_filesystem.processed.name,
    azurerm_storage_data_lake_gen2_filesystem.curated.name
  ]
}
