# Terraform Quick Reference Card

## 🚀 One-Command Deployment

```powershell
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\terraform"; $env:Path += ";C:\Users\$env:USERNAME\terraform;C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"; az login --tenant edc41ca9-a02a-4623-97cb-2a58f19e3c46 --use-device-code; terraform init; terraform apply -auto-approve
```

## 📋 Essential Commands

### Setup
```powershell
# Add tools to PATH
$env:Path += ";C:\Users\$env:USERNAME\terraform;C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"

# Login to Azure
az login --tenant edc41ca9-a02a-4623-97cb-2a58f19e3c46 --use-device-code

# Initialize Terraform
terraform init
```

### Deploy
```powershell
# Preview changes
terraform plan

# Deploy infrastructure
terraform apply

# Deploy without confirmation
terraform apply -auto-approve
```

### Manage
```powershell
# View outputs
terraform output

# Get sensitive value
terraform output -raw storage_account_primary_access_key

# List resources
terraform state list

# Refresh state
terraform refresh
```

### Destroy
```powershell
# Preview destruction
terraform plan -destroy

# Destroy all resources
terraform destroy -auto-approve
```

## 🔑 Current Configuration

| Item | Value |
|------|-------|
| **Subscription** | `12f0f306-0cdf-41a6-9028-a7757690a1e2` |
| **Tenant** | `edc41ca9-a02a-4623-97cb-2a58f19e3c46` |
| **Resource Group** | `urban-cities-rg` |
| **Region** | `West Europe` |
| **Storage Account** | `urbancitiesadls2025` |
| **SQL Server** | `urban-cities-sql-server.database.windows.net` |
| **Database** | `urban_cities_db` |
| **Data Factory** | `urban-cities-adf` |

## 📦 Resources Created

- ✅ Resource Group
- ✅ ADLS Gen2 Storage (raw/processed/curated)
- ✅ Azure Data Factory
- ✅ Azure SQL Server & Database
- ✅ Role Assignments

## 🔧 Troubleshooting

```powershell
# Command not found - Add to PATH
$env:Path += ";C:\Users\$env:USERNAME\terraform"

# Not logged in
az login --use-device-code

# Terraform not initialized
terraform init

# State issues
terraform refresh

# Debug mode
$env:TF_LOG = "DEBUG"
terraform apply
```

## 🌐 Useful URLs

- **Azure Portal**: https://portal.azure.com
- **Terraform Docs**: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs
- **Azure Status**: https://status.azure.com

## 📞 Quick Help

```powershell
# Verify setup
terraform --version
az --version
az account show

# View detailed guide
code COMPREHENSIVE_SETUP_GUIDE.md
```
