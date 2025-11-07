# Urban Cities Infrastructure - Terraform

Production infrastructure for the Urban Cities Service project deployed on Azure.

## 🚀 Quick Start

```powershell
# 1. Ensure prerequisites are installed (Terraform, Azure CLI)
# 2. Login to Azure
az login --tenant edc41ca9-a02a-4623-97cb-2a58f19e3c46 --use-device-code

# 3. Initialize and deploy
terraform init
terraform plan
terraform apply -auto-approve

# 4. View outputs
terraform output
```

## 📋 Documentation

- **[Comprehensive Setup Guide](COMPREHENSIVE_SETUP_GUIDE.md)** - Complete installation and deployment guide
- **[Quick Reference](QUICK_REFERENCE.md)** - Command cheat sheet

## 🏗️ Infrastructure

**Current Deployment:**
- Subscription: `12f0f306-0cdf-41a6-9028-a7757690a1e2`
- Region: West Europe
- Resource Group: `urban-cities-rg`

**Resources:**
- Azure Data Lake Storage Gen2 (`urbancitiesadls2025`)
  - Containers: raw, processed, curated
- Azure Data Factory (`urban-cities-adf`)
- Azure SQL Database (`urban_cities_db`)
  - Server: `urban-cities-sql-server.database.windows.net`

## ⚙️ Configuration

1. Review and customize `terraform.tfvars`:
   ```powershell
   code terraform.tfvars
   ```

2. Key settings:
   - Storage account name (must be globally unique)
   - SQL admin credentials (change for production!)
   - Region and resource naming

## 🔒 Security

**Before Production:**
- [ ] Change SQL admin password in `terraform.tfvars`
- [ ] Review firewall rules
- [ ] Enable resource locks
- [ ] Set up Azure Key Vault for secrets
- [ ] Configure backup policies

## 📊 Management

```powershell
# View resources
terraform state list

# Update infrastructure
terraform plan
terraform apply

# Get connection details
terraform output -json

# Destroy (CAREFUL!)
terraform destroy
```

## 🔧 Troubleshooting

Common issues and solutions are documented in the [Comprehensive Setup Guide](COMPREHENSIVE_SETUP_GUIDE.md#troubleshooting).

## 📞 Support

For detailed documentation, see:
- [COMPREHENSIVE_SETUP_GUIDE.md](COMPREHENSIVE_SETUP_GUIDE.md)
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---

**Version:** 1.0  
**Last Updated:** November 4, 2025  
**Terraform:** v1.13.4  
**Azure Provider:** v3.117.1
