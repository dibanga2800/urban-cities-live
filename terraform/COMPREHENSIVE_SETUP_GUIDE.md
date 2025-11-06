# Urban Cities Infrastructure - Complete Terraform Setup Guide

Complete guide for deploying Azure infrastructure for the Urban Cities Service project using Terraform.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation Guide](#installation-guide)
- [Azure Authentication](#azure-authentication)
- [Configuration](#configuration)
- [Deployment Steps](#deployment-steps)
- [Managing Resources](#managing-resources)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

---

## 🎯 Overview

This Terraform configuration deploys a complete data engineering infrastructure on Azure:

### Resources Created

1. **Resource Group** - Container for all resources
2. **Azure Data Lake Storage Gen2 (ADLS)** - Data lake with hierarchical namespace
   - Container: `raw` - For raw/ingested data
   - Container: `processed` - For transformed data
   - Container: `curated` - For analytics-ready data
3. **Azure Data Factory** - ETL/ELT orchestration with managed identity
4. **Azure SQL Database** - Relational database (Basic tier)
5. **Role Assignments** - Data Factory has Storage Blob Data Contributor access

### Current Deployment

- **Subscription ID**: `12f0f306-0cdf-41a6-9028-a7757690a1e2`
- **Tenant ID**: `edc41ca9-a02a-4623-97cb-2a58f19e3c46`
- **Region**: West Europe
- **Resource Group**: `urban-cities-rg`

---

## 🔧 Prerequisites

### Required Software

1. **Windows PowerShell** (v5.1 or higher) - Pre-installed on Windows
2. **Terraform** (v1.0.0 or higher)
3. **Azure CLI** (v2.0 or higher)

### Azure Requirements

- Active Azure subscription with appropriate permissions
- Ability to create resource groups and resources
- Owner or Contributor role on the subscription

---

## 📥 Installation Guide

### Step 1: Install Azure CLI

#### Option A: Direct Download (Recommended)
1. Download from: https://aka.ms/installazurecliwindows
2. Run the installer (MSI file)
3. Follow the installation wizard
4. Default install location: `C:\Program Files\Microsoft SDKs\Azure\CLI2`

#### Option B: Using Chocolatey
```powershell
# Run PowerShell as Administrator
choco install azure-cli -y
```

#### Verify Installation
```powershell
az --version
```

Expected output:
```
azure-cli                         2.77.0
core                              2.77.0
telemetry                          1.1.0
...
```

### Step 2: Install Terraform

#### Option A: Manual Installation (Recommended for this project)

1. **Download Terraform**:
   - Visit: https://www.terraform.io/downloads
   - Download Windows 64-bit version
   - Extract `terraform.exe` to `C:\Users\<YourUsername>\terraform\`

2. **Add Terraform to PATH**:
   ```powershell
   # Run this script from the terraform directory
   .\add_to_path.ps1
   
   # OR manually add to PATH:
   $terraformPath = "C:\Users\$env:USERNAME\terraform"
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$terraformPath", "User")
   
   # Refresh current session
   $env:Path += ";$terraformPath"
   ```

3. **Verify Installation**:
   ```powershell
   terraform --version
   ```

Expected output:
```
Terraform v1.13.4
on windows_amd64
```

#### Option B: Using Chocolatey
```powershell
# Run PowerShell as Administrator
choco install terraform -y
```

### Step 3: Configure PATH Variables

If commands are not recognized after installation, add them to your PATH:

```powershell
# Add Azure CLI to PATH
$azureCLIPath = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"
$env:Path += ";$azureCLIPath"

# Add Terraform to PATH
$terraformPath = "C:\Users\$env:USERNAME\terraform"
$env:Path += ";$terraformPath"

# Make permanent (User-level)
[Environment]::SetEnvironmentVariable("Path", $env:Path, "User")

# Verify both tools
az --version
terraform --version
```

---

## 🔐 Azure Authentication

### Step 1: Login to Azure

```powershell
# Navigate to the terraform directory
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\terraform"

# Login with device code (recommended for MFA)
az login --use-device-code

# Login with specific tenant
az login --tenant edc41ca9-a02a-4623-97cb-2a58f19e3c46 --use-device-code
```

Follow the prompts:
1. Open https://microsoft.com/devicelogin in your browser
2. Enter the code displayed in the terminal
3. Sign in with your Azure credentials
4. Select your subscription

### Step 2: Verify Authentication

```powershell
# List all subscriptions
az account list --output table

# Show current subscription
az account show

# Expected output:
# {
#   "id": "12f0f306-0cdf-41a6-9028-a7757690a1e2",
#   "name": "Azure subscription 1",
#   "tenantId": "edc41ca9-a02a-4623-97cb-2a58f19e3c46",
#   ...
# }

# Set specific subscription (if needed)
az account set --subscription "12f0f306-0cdf-41a6-9028-a7757690a1e2"
```

### Step 3: Verify Permissions

```powershell
# Check your role assignments
az role assignment list --assignee $(az account show --query user.name -o tsv) --output table
```

You should see Owner or Contributor role on the subscription.

---

## ⚙️ Configuration

### Configuration Files Overview

The project includes these configuration files:

1. **`main.tf`** - Core infrastructure definition
   - Provider configuration (azurerm)
   - Resource group
   - Storage account (ADLS Gen2)
   - Data Factory
   - Azure SQL Server and Database
   - Role assignments

2. **`variables.tf`** - Variable declarations with defaults

3. **`outputs.tf`** - Output values after deployment

4. **`terraform.tfvars`** - Actual configuration values (YOUR VALUES)

### Current Configuration

File: `terraform.tfvars`

```hcl
# Resource Group Configuration
resource_group_name = "urban-cities-rg"
location           = "West Europe"

# Storage Account (ADLS Gen2)
storage_account_name = "urbancitiesadls2025"  # Must be globally unique

# Data Factory
data_factory_name = "urban-cities-adf"

# Azure SQL Server
sql_server_name     = "urban-cities-sql-server"
sql_admin_username  = "sqladmin"
sql_admin_password  = "D030avbang@@"  # Change in production!
sql_database_name   = "urban_cities_db"

# Tags
tags = {
  Environment = "Development"
  Project     = "Urban Cities Service"
  ManagedBy   = "Terraform"
}
```

### Customizing Configuration

To customize for your needs:

```powershell
# Open in editor
notepad terraform.tfvars

# Or use VS Code
code terraform.tfvars
```

**Important Constraints**: 

- `storage_account_name`: 
  - Must be globally unique across all Azure
  - 3-24 characters
  - Lowercase letters and numbers only
  - No hyphens, underscores, or special characters

- `sql_admin_password`: 
  - Minimum 8 characters
  - Must contain uppercase, lowercase, number, and special character
  - Change default for production!

- `location`: Supported regions
  - "West Europe" (default)
  - "North Europe"
  - "UK South"
  - "East US"

---

## 🚀 Deployment Steps

### Complete Deployment Workflow

```powershell
# 1. Navigate to terraform directory
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\terraform"

# 2. Ensure tools are in PATH (add to current session if needed)
$env:Path += ";C:\Users\$env:USERNAME\terraform"
$env:Path += ";C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"

# 3. Login to Azure (if not already logged in)
az login --tenant edc41ca9-a02a-4623-97cb-2a58f19e3c46 --use-device-code

# 4. Verify subscription
az account show

# 5. Initialize Terraform (first time or after changes)
terraform init

# 6. Validate configuration
terraform validate

# 7. Format code (optional - ensures consistent formatting)
terraform fmt

# 8. Review planned changes
terraform plan

# 9. Apply configuration (create resources)
terraform apply

# When prompted, type 'yes' to confirm

# Or apply without confirmation
terraform apply -auto-approve

# 10. View outputs
terraform output

# 11. View sensitive outputs
terraform output -raw storage_account_primary_access_key
terraform output -raw sql_connection_string
```

### Individual Commands Explained

#### terraform init
```powershell
terraform init
```
- Downloads required providers (azurerm)
- Initializes backend
- Creates `.terraform` directory
- Creates `.terraform.lock.hcl` file
- Run this first time and after provider changes

#### terraform plan
```powershell
terraform plan
```
- Shows what will be created/modified/destroyed
- Doesn't make any changes
- Good practice before apply
- Use `-out=plan.tfplan` to save plan

#### terraform apply
```powershell
terraform apply
```
- Creates/updates resources
- Prompts for confirmation
- Shows progress in real-time
- Updates state file

#### terraform output
```powershell
terraform output
```
- Shows all output values
- Use `-json` for JSON format
- Use `-raw` for single values without quotes

### Expected Deployment Output

```
Terraform used the selected providers to generate the following execution plan...

Plan: 10 to add, 0 to change, 0 to destroy.

azurerm_resource_group.main: Creating...
azurerm_resource_group.main: Creation complete after 9s
azurerm_data_factory.main: Creating...
azurerm_mssql_server.main: Creating...
azurerm_storage_account.adls: Creating...
azurerm_data_factory.main: Creation complete after 7s
azurerm_mssql_server.main: Creation complete after 1m21s
azurerm_mssql_firewall_rule.allow_azure_services: Creating...
azurerm_mssql_database.main: Creating...
azurerm_storage_account.adls: Creation complete after 1m4s
azurerm_storage_data_lake_gen2_filesystem.raw: Creating...
azurerm_storage_data_lake_gen2_filesystem.processed: Creating...
azurerm_storage_data_lake_gen2_filesystem.curated: Creating...
azurerm_role_assignment.adf_storage_blob_contributor: Creating...
...
Apply complete! Resources: 10 added, 0 changed, 0 destroyed.

Outputs:

adls_filesystems = [
  "raw",
  "processed",
  "curated",
]
data_factory_id = "/subscriptions/12f0f306-0cdf-41a6-9028-a7757690a1e2/..."
data_factory_name = "urban-cities-adf"
resource_group_name = "urban-cities-rg"
sql_connection_string = <sensitive>
sql_database_name = "urban_cities_db"
sql_server_fqdn = "urban-cities-sql-server.database.windows.net"
storage_account_name = "urbancitiesadls2025"
storage_account_primary_access_key = <sensitive>
storage_account_primary_endpoint = "https://urbancitiesadls2025.dfs.core.windows.net/"
```

### Deployment Timeline

| Resource | Time | Notes |
|----------|------|-------|
| Resource Group | ~10 seconds | Fast |
| Data Factory | ~10 seconds | Fast |
| SQL Server | ~1-2 minutes | Moderate |
| SQL Database | ~2-3 minutes | Slowest |
| Storage Account | ~1 minute | Moderate |
| Storage Containers | ~1 second each | Very fast |
| Role Assignment | ~20-30 seconds | Fast |
| **Total** | **5-7 minutes** | Approximate |

---

## 📊 Managing Resources

### View Resource State

```powershell
# List all resources managed by Terraform
terraform state list

# Example output:
# azurerm_resource_group.main
# azurerm_storage_account.adls
# azurerm_data_factory.main
# azurerm_mssql_server.main
# azurerm_mssql_database.main
# ...

# Show details of specific resource
terraform state show azurerm_storage_account.adls

# View entire current state
terraform show

# View state in JSON format
terraform show -json | ConvertFrom-Json
```

### Update Resources

```powershell
# 1. Make changes to terraform.tfvars or *.tf files
# Example: Change location from "West Europe" to "North Europe"

# 2. Preview changes
terraform plan

# 3. Apply changes
terraform apply

# Terraform will show what will be modified/recreated
# Some changes require resource replacement (destroy + create)
```

### Destroy Resources

```powershell
# Preview what will be destroyed
terraform plan -destroy

# Destroy specific resource
terraform destroy -target=azurerm_mssql_database.main

# Destroy all resources (CAREFUL!)
terraform destroy

# Destroy without confirmation (VERY CAREFUL!)
terraform destroy -auto-approve
```

**⚠️ Warning**: Destroying resources will permanently delete them and all their data!

### Refresh State

```powershell
# Refresh state from Azure (check for drift)
terraform refresh

# Or during plan/apply
terraform plan -refresh=true
terraform apply -refresh=true
```

### Import Existing Resources

If you created resources manually and want to manage them with Terraform:

```powershell
# Import syntax
terraform import <resource_type>.<name> <azure_resource_id>

# Example: Import existing storage account
terraform import azurerm_storage_account.adls /subscriptions/12f0f306-0cdf-41a6-9028-a7757690a1e2/resourceGroups/urban-cities-rg/providers/Microsoft.Storage/storageAccounts/urbancitiesadls2025
```

---

## 🔐 Environment Variables

### For Application Use

Create a `.env` file for your applications (template in `.env.example`):

```bash
# Azure SQL Database Connection
SQL_SERVER=urban-cities-sql-server.database.windows.net
SQL_DATABASE=urban_cities_db
SQL_USERNAME=sqladmin
SQL_PASSWORD=D030avbang@@
SQL_PORT=1433
SQL_DRIVER={ODBC Driver 17 for SQL Server}

# Connection String (for apps that use connection strings)
SQL_CONNECTION_STRING=Server=tcp:urban-cities-sql-server.database.windows.net,1433;Initial Catalog=urban_cities_db;Persist Security Info=False;User ID=sqladmin;Password=D030avbang@@;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;

# Azure Data Lake Storage Gen2
ADLS_ACCOUNT_NAME=urbancitiesadls2025
ADLS_ACCOUNT_KEY=<get from terraform output>
ADLS_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=urbancitiesadls2025;AccountKey=<key>;EndpointSuffix=core.windows.net
ADLS_CONTAINER_RAW=raw
ADLS_CONTAINER_PROCESSED=processed
ADLS_CONTAINER_CURATED=curated
ADLS_ENDPOINT=https://urbancitiesadls2025.dfs.core.windows.net/

# Azure Data Factory
ADF_NAME=urban-cities-adf
ADF_RESOURCE_GROUP=urban-cities-rg
ADF_ID=/subscriptions/12f0f306-0cdf-41a6-9028-a7757690a1e2/resourceGroups/urban-cities-rg/providers/Microsoft.DataFactory/factories/urban-cities-adf

# Azure Configuration
AZURE_SUBSCRIPTION_ID=12f0f306-0cdf-41a6-9028-a7757690a1e2
AZURE_TENANT_ID=edc41ca9-a02a-4623-97cb-2a58f19e3c46
AZURE_LOCATION=westeurope
```

### Get Sensitive Values from Terraform

```powershell
# Get storage account key
terraform output -raw storage_account_primary_access_key

# Get SQL connection string
terraform output -raw sql_connection_string

# Export all outputs to JSON file
terraform output -json > outputs.json

# Or pretty-print
terraform output -json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Load Environment Variables in PowerShell

```powershell
# Load .env file
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

# Verify
$env:SQL_SERVER
$env:ADLS_ACCOUNT_NAME
```

### Load Environment Variables in Python

```python
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Access variables
sql_server = os.getenv('SQL_SERVER')
storage_account = os.getenv('ADLS_ACCOUNT_NAME')
```

---

## 🔍 Troubleshooting

### Issue: "terraform: command not found"

**Cause**: Terraform not in PATH

**Solution**:
```powershell
# Check if Terraform executable exists
Test-Path "C:\Users\$env:USERNAME\terraform\terraform.exe"

# Add to current session
$env:Path += ";C:\Users\$env:USERNAME\terraform"

# Or run the PATH script
.\add_to_path.ps1

# Verify
terraform --version

# Make permanent
[Environment]::SetEnvironmentVariable("Path", $env:Path, "User")
```

### Issue: "az: command not found"

**Cause**: Azure CLI not in PATH

**Solution**:
```powershell
# Check if Azure CLI exists
Test-Path "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"

# Add to current session
$env:Path += ";C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"

# Verify
az --version

# Make permanent
[Environment]::SetEnvironmentVariable("Path", $env:Path, "User")
```

### Issue: "Please run 'az login' to setup account"

**Cause**: Not authenticated with Azure

**Solution**:
```powershell
# Logout first (clear any cached credentials)
az logout

# Login with device code
az login --tenant edc41ca9-a02a-4623-97cb-2a58f19e3c46 --use-device-code

# Follow the browser prompts

# Verify login
az account show

# Should show your subscription details
```

### Issue: "ConflictingConcurrentWriteNotAllowed"

**Cause**: Multiple resource provider registrations happening simultaneously

**Solution**: Already handled in `main.tf` with:
```hcl
skip_provider_registration = true
```

If you still see this error, wait 5 minutes and retry.

### Issue: "StorageAccountAlreadyTaken"

**Cause**: Storage account names must be globally unique across all of Azure

**Solution**:
```powershell
# Edit terraform.tfvars
# Change: storage_account_name = "urbancitiesadls2025"
# To:     storage_account_name = "urbancitiesadls2026"
# Or:     storage_account_name = "urbancitiesyourname2025"

notepad terraform.tfvars

# Apply changes
terraform apply
```

### Issue: "LocationIsOfferRestricted" or "ProvisioningDisabled"

**Cause**: Your subscription doesn't support that resource in the selected region

**Solution**:
```powershell
# Try different regions in terraform.tfvars
# Change location = "West Europe"
# Try: "North Europe", "UK South", "West US"

notepad terraform.tfvars

# Reinitialize and apply
terraform init -reconfigure
terraform apply
```

### Issue: "Provider produced inconsistent result"

**Cause**: Azure API issue or network connectivity problem

**Solution**:
```powershell
# Option 1: Wait 2-5 minutes and retry
terraform apply

# Option 2: Destroy and recreate
terraform destroy -auto-approve
terraform apply -auto-approve

# Option 3: Check Azure service health
# Visit: https://status.azure.com/
```

### Issue: Connection timeout to Azure API

**Cause**: Network issues or Azure service problems

**Solution**:
```powershell
# Check internet connection
Test-NetConnection portal.azure.com -Port 443

# Check Azure login
az account show

# Retry with longer timeout
$env:ARM_CLIENT_TIMEOUT = "60"
terraform apply
```

### Issue: "Error locking state"

**Cause**: Previous Terraform operation didn't complete properly

**Solution**:
```powershell
# Force unlock (use the lock ID from error message)
terraform force-unlock <LOCK_ID>

# Example:
# terraform force-unlock a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Issue: Changes not reflecting

**Cause**: State drift between Terraform and Azure

**Solution**:
```powershell
# Refresh state
terraform refresh

# Re-plan
terraform plan

# Apply if needed
terraform apply
```

---

## 🔒 Security Best Practices

### 1. Credentials Management

```powershell
# ❌ NEVER commit these files to version control:
terraform.tfvars          # Contains passwords
terraform.tfstate         # Contains sensitive data  
terraform.tfstate.backup  # Backup of state
.terraform/               # Provider files
.env                      # Environment variables
*.tfvars                  # Variable files

# ✅ Already configured in .gitignore
# Verify:
cat .gitignore
```

### 2. Change Default Passwords

**IMPORTANT**: Change the default SQL admin password before production use!

```powershell
# Edit terraform.tfvars
notepad terraform.tfvars

# Change:
sql_admin_password = "D030avbang@@"

# To something strong like:
sql_admin_password = "MyStr0ng!P@ssw0rd2025"

# Requirements:
# - Minimum 8 characters
# - At least 1 uppercase letter
# - At least 1 lowercase letter
# - At least 1 number
# - At least 1 special character

# Apply changes
terraform apply
```

### 3. Use Azure Key Vault (Production)

For production, store secrets in Azure Key Vault:

```powershell
# Create Key Vault
az keyvault create `
  --name "urban-cities-kv" `
  --resource-group "urban-cities-rg" `
  --location "westeurope"

# Store SQL password
az keyvault secret set `
  --vault-name "urban-cities-kv" `
  --name "sql-admin-password" `
  --value "YourStrongPassword123!"

# Store Storage Account Key
$storageKey = terraform output -raw storage_account_primary_access_key
az keyvault secret set `
  --vault-name "urban-cities-kv" `
  --name "storage-account-key" `
  --value $storageKey

# Retrieve secret
az keyvault secret show `
  --vault-name "urban-cities-kv" `
  --name "sql-admin-password" `
  --query "value" -o tsv
```

### 4. Limit Network Access

Add IP-based firewall rules to restrict access:

```powershell
# Get your public IP
$myIP = (Invoke-WebRequest -Uri "https://api.ipify.org").Content

# Add firewall rule for SQL Server
az sql server firewall-rule create `
  --resource-group "urban-cities-rg" `
  --server "urban-cities-sql-server" `
  --name "AllowMyIP" `
  --start-ip-address $myIP `
  --end-ip-address $myIP

# Or add to main.tf:
```

```hcl
resource "azurerm_mssql_firewall_rule" "allow_my_ip" {
  name             = "AllowMyIP"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = "YOUR_IP_ADDRESS"
  end_ip_address   = "YOUR_IP_ADDRESS"
}
```

### 5. Enable Terraform State Encryption

For team collaboration, use Azure Storage backend:

```hcl
# Add to main.tf at the top:
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "tfstateurbancities"
    container_name       = "tfstate"
    key                  = "urban-cities.tfstate"
    use_azuread_auth     = true
  }
}
```

```powershell
# Create storage account for state
az group create --name "terraform-state-rg" --location "westeurope"
az storage account create `
  --name "tfstateurbancities" `
  --resource-group "terraform-state-rg" `
  --location "westeurope" `
  --sku "Standard_LRS"
az storage container create `
  --name "tfstate" `
  --account-name "tfstateurbancities"

# Reinitialize
terraform init -reconfigure
```

### 6. Enable Resource Locks

Prevent accidental deletion:

```powershell
# Lock resource group
az lock create `
  --name "DoNotDelete" `
  --resource-group "urban-cities-rg" `
  --lock-type CanNotDelete

# View locks
az lock list --resource-group "urban-cities-rg"

# Remove lock (when needed)
az lock delete --name "DoNotDelete" --resource-group "urban-cities-rg"
```

### 7. Enable Audit Logging

```powershell
# Enable SQL audit logging
az sql server audit-policy update `
  --resource-group "urban-cities-rg" `
  --server "urban-cities-sql-server" `
  --state Enabled `
  --storage-account "urbancitiesadls2025"
```

---

## 📚 Additional Resources

### Official Documentation

- [Terraform Documentation](https://www.terraform.io/docs)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure CLI Documentation](https://docs.microsoft.com/en-us/cli/azure/)
- [Azure Data Lake Storage Gen2](https://docs.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-introduction)
- [Azure Data Factory](https://docs.microsoft.com/en-us/azure/data-factory/)
- [Azure SQL Database](https://docs.microsoft.com/en-us/azure/azure-sql/)

### Project-Specific Files

| File | Purpose |
|------|---------|
| `main.tf` | Core infrastructure definition |
| `variables.tf` | Variable declarations with defaults |
| `outputs.tf` | Output definitions |
| `terraform.tfvars` | Your configuration values |
| `terraform.tfvars.example` | Example configuration |
| `.gitignore` | Files to exclude from git |
| `add_to_path.ps1` | PATH configuration script |
| `setup.ps1` | Automated setup script |
| `quickstart.ps1` | Interactive deployment |
| `azure_connection_examples.py` | Python connection examples |
| `.env.example` | Environment variables template |

### Quick Reference Commands

```powershell
# Initialization & Planning
terraform init                    # Initialize working directory
terraform init -reconfigure       # Reconfigure backend
terraform validate               # Validate configuration
terraform fmt                    # Format code
terraform plan                   # Preview changes
terraform plan -out=plan.tfplan  # Save plan to file

# Deployment
terraform apply                  # Apply changes (with confirmation)
terraform apply -auto-approve    # Apply without confirmation
terraform apply plan.tfplan      # Apply saved plan

# State Management
terraform state list             # List resources
terraform state show <resource>  # Show resource details
terraform refresh                # Refresh state
terraform show                   # Show current state

# Outputs
terraform output                 # Show all outputs
terraform output <name>          # Show specific output
terraform output -json           # JSON format
terraform output -raw <name>     # Raw value (no quotes)

# Destruction
terraform plan -destroy          # Preview destruction
terraform destroy                # Destroy resources
terraform destroy -auto-approve  # Destroy without confirmation

# Workspace Management (for multiple environments)
terraform workspace list         # List workspaces
terraform workspace new <name>   # Create workspace
terraform workspace select <name> # Switch workspace

# Azure CLI
az login                         # Login to Azure
az logout                        # Logout
az account list                  # List subscriptions
az account show                  # Show current subscription
az account set --subscription ID # Set subscription
```

### Connection Examples

#### Python - SQL Database

```python
import pyodbc
import os

# Using environment variables
server = os.getenv('SQL_SERVER')
database = os.getenv('SQL_DATABASE')
username = os.getenv('SQL_USERNAME')
password = os.getenv('SQL_PASSWORD')

connection_string = (
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password}'
)

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()
cursor.execute("SELECT @@VERSION")
row = cursor.fetchone()
print(row)
```

#### Python - ADLS Gen2

```python
from azure.storage.filedatalake import DataLakeServiceClient
import os

account_name = os.getenv('ADLS_ACCOUNT_NAME')
account_key = os.getenv('ADLS_ACCOUNT_KEY')

service_client = DataLakeServiceClient(
    account_url=f"https://{account_name}.dfs.core.windows.net",
    credential=account_key
)

# List filesystems
filesystems = service_client.list_file_systems()
for fs in filesystems:
    print(fs.name)

# Upload file
file_system_client = service_client.get_file_system_client("raw")
file_client = file_system_client.get_file_client("test.csv")
with open("local_file.csv", "rb") as data:
    file_client.upload_data(data, overwrite=True)
```

---

## 📞 Support & Troubleshooting

### Getting Help

1. **Check this guide** - Most common issues are covered above
2. **Review Terraform logs** - Use `TF_LOG=DEBUG terraform apply`
3. **Check Azure service health** - https://status.azure.com/
4. **Terraform documentation** - https://www.terraform.io/docs
5. **Azure documentation** - https://docs.microsoft.com/en-us/azure/

### Enable Debug Logging

```powershell
# Enable Terraform debug logging
$env:TF_LOG = "DEBUG"
$env:TF_LOG_PATH = "terraform-debug.log"

# Run command
terraform apply

# Review log
notepad terraform-debug.log

# Disable logging
$env:TF_LOG = ""
$env:TF_LOG_PATH = ""
```

### Common Error Patterns

| Error Pattern | Likely Cause | Solution |
|---------------|-------------|----------|
| "command not found" | PATH issue | Add tool to PATH |
| "Please run az login" | Not authenticated | Run `az login` |
| "AlreadyExists" | Resource name conflict | Change resource name |
| "LocationNotAvailable" | Region restriction | Try different region |
| "QuotaExceeded" | Subscription limit | Request quota increase |
| "Unauthorized" | Permission issue | Check RBAC roles |
| "Timeout" | Network/Azure issue | Retry after waiting |

### Verify Complete Setup

Run this verification script:

```powershell
# Verification Script
Write-Host "=== Terraform Setup Verification ===" -ForegroundColor Cyan

# Check Terraform
if (Get-Command terraform -ErrorAction SilentlyContinue) {
    Write-Host "✓ Terraform installed: $(terraform --version | Select-Object -First 1)" -ForegroundColor Green
} else {
    Write-Host "✗ Terraform not found" -ForegroundColor Red
}

# Check Azure CLI
if (Get-Command az -ErrorAction SilentlyContinue) {
    Write-Host "✓ Azure CLI installed: $(az --version | Select-String 'azure-cli')" -ForegroundColor Green
} else {
    Write-Host "✗ Azure CLI not found" -ForegroundColor Red
}

# Check Azure login
try {
    $account = az account show | ConvertFrom-Json
    Write-Host "✓ Logged in to Azure: $($account.name)" -ForegroundColor Green
} catch {
    Write-Host "✗ Not logged in to Azure" -ForegroundColor Red
}

# Check Terraform initialization
if (Test-Path ".terraform") {
    Write-Host "✓ Terraform initialized" -ForegroundColor Green
} else {
    Write-Host "✗ Terraform not initialized (run 'terraform init')" -ForegroundColor Yellow
}

# Check state file
if (Test-Path "terraform.tfstate") {
    Write-Host "✓ Terraform state exists" -ForegroundColor Green
} else {
    Write-Host "ℹ No terraform state (no resources deployed yet)" -ForegroundColor Yellow
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
```

---

## 🎓 Learning Resources

### Terraform Learning Path

1. **Terraform Basics** - https://learn.hashicorp.com/terraform
2. **Azure Provider** - https://learn.hashicorp.com/collections/terraform/azure-get-started
3. **State Management** - https://www.terraform.io/docs/language/state/index.html
4. **Best Practices** - https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html

### Azure Learning Path

1. **Azure Fundamentals** - https://docs.microsoft.com/en-us/learn/paths/azure-fundamentals/
2. **Data Engineering on Azure** - https://docs.microsoft.com/en-us/learn/paths/data-engineering-with-databricks/
3. **Azure Data Factory** - https://docs.microsoft.com/en-us/learn/modules/intro-to-azure-data-factory/

---

## 📝 Changelog

### Version 1.0 - November 4, 2025

**Initial Release**
- Complete Terraform configuration for Urban Cities infrastructure
- Azure SQL Database (replaced PostgreSQL)
- ADLS Gen2 with three containers (raw/processed/curated)
- Azure Data Factory with managed identity
- Automated role assignments
- Comprehensive documentation

**Infrastructure Details**
- Subscription: 12f0f306-0cdf-41a6-9028-a7757690a1e2
- Region: West Europe
- Terraform: v1.13.4
- Azure Provider: v3.117.1

---

**Last Updated**: November 4, 2025  
**Maintained By**: Data Engineering Team  
**Terraform Version**: 1.13.4  
**Azure Provider Version**: 3.117.1  
**Status**: ✅ Production Ready
