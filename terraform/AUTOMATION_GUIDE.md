# Complete Infrastructure Automation Guide

## Overview
This guide covers the fully automated deployment of the Urban Cities Service infrastructure using Terraform. The automation creates all Azure resources, configures permissions, and sets up the data pipeline with zero manual intervention.

## Prerequisites

### Required Software
- **Terraform**: Installed at `C:\Users\David Ibanga\terraform\terraform.exe`
- **Azure CLI**: Installed at `C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin`
- **Python**: 3.13+ with required packages (pyodbc, azure-storage-file-datalake, azure-identity, azure-mgmt-datafactory, python-dotenv)
- **Astronomer Astro CLI**: v1.38.0 for Airflow orchestration

### Azure Prerequisites
- **Service Principal**: Already created with ID `27b470a2-fa5d-458a-85d5-e639c0791f23`
- **Object ID**: `9306b861-8960-496a-9a0d-3f996df4a7fb` (used for role assignments)
- **Subscription**: `12f0f306-0cdf-41a6-9028-a7757690a1e2`
- **Tenant**: `edc41ca9-a02a-4623-97cb-2a58f19e3c46`
- **Azure CLI**: Authenticated (`az login`)

## One-Command Deployment

```powershell
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\terraform"
$env:Path += ";C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"
& "C:\Users\David Ibanga\terraform\terraform.exe" apply -auto-approve
```

**Duration**: Approximately 21 minutes (SQL Server creation takes 15-20 minutes)

## What Gets Created

### Infrastructure Resources (14 total)

1. **Resource Group** (`urban-cities-rg`)
   - Location: West Europe
   - Contains all project resources
   - Tags: Environment, Project, ManagedBy

2. **Azure Data Lake Storage Gen2** (`urbancitiesadls2025`)
   - Hierarchical namespace enabled
   - 3 containers created automatically:
     - `raw`: Raw data from NYC 311 API
     - `processed`: Transformed/cleaned data
     - `curated`: Aggregated analytics-ready data

3. **Azure Data Factory** (`urban-cities-adf`)
   - System-assigned managed identity
   - Linked services and pipeline created via provisioner
   - Auto-configured with Storage and SQL connections

4. **Azure SQL Server** (`urban-cities-sql-srv-2025`)
   - Fully qualified domain name: `urban-cities-sql-srv-2025.database.windows.net`
   - Admin username: `sqladmin`
   - Admin password: From terraform.tfvars (sensitive)
   - Creation time: 15-20 minutes

5. **Azure SQL Database** (`urban_cities_db`)
   - Service tier: Basic
   - Max size: 2GB
   - 27-column schema created via provisioner
   - 6 indexes for optimized queries

6. **Firewall Rules** (2 rules)
   - **Azure Services**: Allows Azure services to access SQL Server
   - **Current IP**: Automatically detects and allows your public IP (109.154.172.101)
   - IP detection via HTTP provider: `https://api.ipify.org?format=text`

7. **Role Assignments** (2 assignments)
   - **ADF → Storage**: Data Factory managed identity gets Storage Blob Data Contributor role
   - **Service Principal → ADF**: Service Principal gets Data Factory Contributor role
   - Enables automated pipeline creation and data movement

### Automated Configuration (via Provisioners)

8. **SQL Table Creation** (`nyc_311_requests`)
   - 27 columns matching NYC 311 API schema
   - Primary key on `unique_key`
   - 6 indexes:
     - idx_created_date
     - idx_agency
     - idx_complaint_type
     - idx_status
     - idx_borough
     - idx_location_coords
   - Provisioner runs automatically, fails gracefully if issues occur

9. **ADF Pipeline Creation** (`CopyProcessedDataToSQL`)
   - ADLS Gen2 Linked Service
   - Azure SQL Database Linked Service
   - Dataset: Processed container CSV files
   - Pipeline: Automated copy from ADLS to SQL
   - Provisioner runs automatically after role propagation

## Infrastructure Outputs

After successful deployment, Terraform outputs:

```hcl
adls_filesystems              = ["raw", "processed", "curated"]
data_factory_id               = "/subscriptions/.../urban-cities-adf"
data_factory_name             = "urban-cities-adf"
resource_group_name           = "urban-cities-rg"
sql_connection_string         = <sensitive>
sql_database_name             = "urban_cities_db"
sql_server_fqdn              = "urban-cities-sql-srv-2025.database.windows.net"
storage_account_name          = "urbancitiesadls2025"
storage_account_primary_access_key = <sensitive>
storage_account_primary_endpoint   = "https://urbancitiesadls2025.dfs.core.windows.net/"
```

## Configuration Files

### terraform.tfvars
```hcl
# Azure Resource Configuration
resource_group_name   = "urban-cities-rg"
location              = "West Europe"
storage_account_name  = "urbancitiesadls2025"
data_factory_name     = "urban-cities-adf"
sql_server_name       = "urban-cities-sql-srv-2025"
sql_database_name     = "urban_cities_db"

# SQL Credentials (sensitive)
sql_admin_username = "sqladmin"
sql_admin_password = "D030avbang@@"
```

### Environment Variables (.env files)
Located in:
- `astro-airflow/.env` (for Airflow DAGs)
- `notebook/.env` (for standalone scripts)

Key variables:
```bash
AZURE_TENANT_ID=edc41ca9-a02a-4623-97cb-2a58f19e3c46
AZURE_CLIENT_ID=27b470a2-fa5d-458a-85d5-e639c0791f23
AZURE_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
AZURE_SUBSCRIPTION_ID=12f0f306-0cdf-41a6-9028-a7757690a1e2
ADLS_ACCOUNT_NAME=urbancitiesadls2025
SQL_SERVER=urban-cities-sql-srv-2025.database.windows.net
SQL_DATABASE=urban_cities_db
```

## Complete Workflow

### 1. Infrastructure Deployment
```powershell
terraform apply -auto-approve
```

### 2. Verify SQL Table Creation
```powershell
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\notebook"
python check_table.py
```

Expected output:
```
Database: urban_cities_db
Server: urban-cities-sql-srv-2025.database.windows.net
Tables found: 1
  - nyc_311_requests
Table 'nyc_311_requests' has 0 rows
```

### 3. Start Airflow (Astro)
```powershell
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\astro-airflow"
astro dev start
```

### 4. Access Airflow UI
- URL: http://localhost:8080
- Username: `admin`
- Password: `admin`

### 5. Run ETL Pipeline
- Navigate to DAGs page
- Find: `nyc_311_incremental_etl_azure`
- Click "Unpause" toggle
- Click "Trigger DAG" play button

### 6. Monitor Pipeline Execution
The DAG executes 9 tasks in sequence:
1. ✅ **start**: Initialize pipeline
2. ✅ **extract_data**: Fetch from NYC 311 API (https://data.cityofnewyork.us/resource/erm2-nwe9.json)
3. ✅ **transform_data**: Clean, validate, derive columns
4. ✅ **load_to_azure**: Upload to ADLS Gen2 (raw + processed)
5. ✅ **trigger_adf_pipeline**: Execute ADF pipeline to copy to SQL
6. ✅ **update_state**: Save ETL timestamp to `/usr/local/airflow/include/data/etl_state.json`
7. ✅ **cleanup_temp_files**: Remove local temp files
8. ✅ **send_notification**: Log completion status
9. ✅ **end**: Pipeline complete

### 7. Verify Data in SQL
```powershell
python check_table.py
```

Expected output:
```
Table 'nyc_311_requests' has 42000+ rows
```

### 8. Verify Data in ADLS
```powershell
az storage fs file list --account-name urbancitiesadls2025 --file-system raw --auth-mode login
az storage fs file list --account-name urbancitiesadls2025 --file-system processed --auth-mode login
```

## Destroy Infrastructure

To completely remove all Azure resources:

```powershell
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\terraform"
& "C:\Users\David Ibanga\terraform\terraform.exe" destroy -auto-approve
```

**Duration**: Approximately 2 minutes

**Resources destroyed**: 13 total (provisioners don't count as resources)

## Automation Features

### 1. Automatic IP Detection
- Uses HTTP provider to query `https://api.ipify.org?format=text`
- Dynamically adds your current public IP to SQL firewall rules
- No hardcoded IPs in configuration
- Updates automatically on each apply

### 2. Role Propagation Handling
- Service Principal → Data Factory assignment happens early in deployment
- ADF pipeline provisioner depends on role assignment completion
- 5-10 minute propagation time built into dependency chain

### 3. Graceful Provisioner Failures
- Both provisioners configured with `on_failure = continue`
- Infrastructure creates successfully even if provisioners fail
- Manual execution option available:
  ```powershell
  python notebook/create_sql_table.py
  python notebook/create_adf_pipeline.py
  ```

### 4. State Management
- Terraform state stored locally: `terraform.tfstate`
- Backup state: `terraform.tfstate.backup`
- For production, migrate to Azure Storage backend

### 5. Sensitive Data Protection
- SQL credentials marked as sensitive
- Storage keys marked as sensitive
- Outputs show `<sensitive>` instead of actual values
- Retrieve with: `terraform output sql_connection_string`

## Troubleshooting

### Issue: SQL Server Creation Takes Too Long
**Symptom**: Apply hangs at "azurerm_mssql_server.main: Creating..."

**Solution**: This is normal. Azure SQL Server provisioning takes 15-20 minutes. Do not interrupt.

### Issue: Role Assignment Propagation Delay
**Symptom**: ADF pipeline provisioner fails with AuthorizationFailed

**Solution**: 
1. Check if provisioner has `on_failure = continue` (should be present)
2. Wait 5-10 minutes for role propagation
3. Manually run: `python notebook/create_adf_pipeline.py`

### Issue: Firewall Rule Blocks Connection
**Symptom**: Cannot connect to SQL Server from local machine

**Solution**:
1. Verify your IP: `curl https://api.ipify.org`
2. Check if IP changed: `terraform refresh`
3. Update firewall: `terraform apply -auto-approve`

### Issue: Provisioner Encoding Errors
**Symptom**: Provisioner output shows encoding characters instead of Unicode symbols

**Solution**: This is cosmetic. Provisioners are configured with `on_failure = continue`. If table/pipeline not created, run scripts manually:
```powershell
cd notebook
python create_sql_table.py
python create_adf_pipeline.py
```

### Issue: Terraform State Lock
**Symptom**: "Error acquiring the state lock"

**Solution**: State stored locally, should not lock. If issue persists:
```powershell
Remove-Item .terraform.tfstate.lock.info -Force
```

### Issue: ADF Pipeline Not Found
**Symptom**: Airflow task `trigger_adf_pipeline` fails

**Solution**: Run pipeline creation manually:
```powershell
cd notebook
python create_adf_pipeline.py
```

## Production Readiness

### Current State: Development/Testing ✅

### Production Enhancements Needed:

1. **Remote State Backend**
   ```hcl
   terraform {
     backend "azurerm" {
       resource_group_name  = "terraform-state-rg"
       storage_account_name = "tfstateurbancities"
       container_name       = "tfstate"
       key                  = "urban-cities.terraform.tfstate"
     }
   }
   ```

2. **Azure Key Vault Integration**
   - Store SQL credentials in Key Vault
   - Reference secrets from Terraform
   - Rotate credentials programmatically

3. **Environment Separation**
   - Create separate workspaces: dev, staging, prod
   - Use `-var-file=prod.tfvars` for different environments
   - Separate Azure subscriptions recommended

4. **Monitoring & Alerts**
   - Azure Monitor workspaces
   - Application Insights for Airflow
   - Cost alerts and budgets
   - Data quality monitoring

5. **CI/CD Pipeline**
   - GitHub Actions or Azure DevOps
   - Automated terraform plan on PR
   - Automated terraform apply on merge to main
   - Environment-specific approvals

6. **Security Hardening**
   - Private endpoints for Storage and SQL
   - VNet integration for Data Factory
   - Managed identities instead of Service Principal
   - Key rotation policies

7. **Disaster Recovery**
   - Geo-redundant storage (GRS)
   - SQL Database backup policies
   - Terraform state backup strategy
   - Runbook for recovery procedures

8. **Cost Optimization**
   - SQL Database: Basic → S0 or Serverless
   - ADLS: Lifecycle management policies (Hot → Cool → Archive)
   - ADF: Activity-based pricing monitoring
   - Reserved capacity for predictable workloads

## Known Limitations

1. **SQL Server Provisioning Time**: 15-20 minutes is unavoidable with current Azure SQL pricing tier
2. **Role Propagation Delay**: Azure AD can take 5-10 minutes to propagate role assignments
3. **Windows CMD Encoding**: Unicode characters in Python output may display incorrectly in provisioners
4. **Service Principal Pre-requisite**: Must be created outside Terraform currently
5. **Local State**: Not suitable for team collaboration without remote backend

## Future Enhancements

1. **Automated Testing**: Terratest integration for infrastructure validation
2. **Multi-Region Deployment**: Failover and load balancing across regions
3. **Data Retention Policies**: Automated archival and deletion of old data
4. **Advanced Analytics**: Integration with Azure Synapse Analytics
5. **Real-time Processing**: Azure Stream Analytics for hot path
6. **Machine Learning**: Azure ML integration for predictive analytics
7. **Cost Dashboard**: Power BI dashboard for infrastructure costs
8. **Compliance Scanning**: Azure Policy and Defender for Cloud
9. **Performance Monitoring**: Query Performance Insights for SQL
10. **Auto-scaling**: Dynamic scaling based on workload patterns

## Support & Maintenance

### Regular Tasks
- **Weekly**: Review Airflow DAG runs and failure logs
- **Monthly**: Review Azure costs and optimize resources
- **Quarterly**: Update Terraform provider versions
- **Annually**: Review and update Service Principal credentials

### Health Checks
```powershell
# Infrastructure health
terraform plan  # Should show no changes

# Airflow health
astro dev ps  # All containers running

# Azure resources health
az resource list --resource-group urban-cities-rg --output table

# SQL Database health
python notebook/check_table.py
```

### Documentation
- **Main README**: Project overview and setup
- **MIGRATION_NOTES**: Astro migration details
- **QUICK_START**: Step-by-step startup guide
- **This Guide**: Complete automation reference

## Conclusion

This automation framework provides a reproducible, documented, and maintainable infrastructure deployment process. With a single command, you can deploy the entire Urban Cities Service platform to Azure, enabling seamless development, testing, and production workflows.

For questions or issues, review the troubleshooting section or check the Terraform output for detailed error messages.

**Last Updated**: 2025-11-05
**Terraform Version**: 1.5+
**Azure Provider Version**: 3.0+
**Maintained By**: Infrastructure Team
