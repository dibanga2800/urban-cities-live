# Setup Guide

This guide walks you through setting up the NYC 311 ETL pipeline from scratch.

## Prerequisites

Install the following tools before proceeding:

- **Azure CLI** - [Installation Guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
- **Terraform** 1.5+ - [Download](https://www.terraform.io/downloads)
- **Astronomer Astro CLI** 1.38+ - [Installation Guide](https://docs.astronomer.io/astro/cli/install-cli)
- **Python** 3.11+ - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)

Verify installations:
```powershell
az --version
terraform --version
astro version
python --version
git --version
```

## Step 1: Azure Setup

### Login to Azure
```powershell
az login
```

### Set Active Subscription
```powershell
# List available subscriptions
az account list --output table

# Set active subscription
az account set --subscription "Your Subscription Name"

# Verify
az account show
```

## Step 2: Clone Repository

```powershell
git clone <repository-url>
cd Urban_Cities_live_Service
```

## Step 3: Configure Terraform

### Create Variables File
```powershell
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

### Edit `terraform.tfvars`
```hcl
# Required values
resource_group_name  = "urban-cities-rg"
location             = "eastus"
storage_account_name = "urbancitiesadls2025"  # Must be globally unique
data_factory_name    = "urban-cities-adf"
sql_server_name      = "urban-cities-sql-srv-2025"  # Must be globally unique
sql_database_name    = "urban_cities_db"
sql_admin_username   = "sqladmin"
sql_admin_password   = "YourSecurePassword123!"  # Change this!

# Optional: Will auto-detect if not provided
client_ip_address    = ""
```

### Deploy Infrastructure
```powershell
terraform init
terraform plan
terraform apply
```

**This takes ~10-15 minutes and creates:**
- Resource Group
- Storage Account (ADLS Gen2) with 3 containers
- Data Factory
- SQL Server and Database
- Service Principal (optional)
- Firewall rules

### Save Outputs
```powershell
terraform output > ../deployment-outputs.txt
```

## Step 4: Create Service Principal

### Option A: Using Azure Portal
1. Navigate to Azure Active Directory
2. Go to App registrations → New registration
3. Name: `urban-cities-sp`
4. Click Register
5. Go to Certificates & secrets → New client secret
6. Copy the client ID and secret

### Option B: Using Azure CLI
```powershell
# Create service principal
az ad sp create-for-rbac --name urban-cities-sp --role Contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/urban-cities-rg

# Output will show:
# {
#   "appId": "xxx",        # This is CLIENT_ID
#   "password": "xxx",     # This is CLIENT_SECRET
#   "tenant": "xxx"        # This is TENANT_ID
# }
```

### Assign Storage Permission
```powershell
az role assignment create \
  --assignee {client-id-from-above} \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/{subscription-id}/resourceGroups/urban-cities-rg/providers/Microsoft.Storage/storageAccounts/urbancitiesadls2025
```

## Step 5: Configure Environment Variables

### Create `.env` File
```powershell
cd ..\astro-airflow
New-Item -ItemType File -Path .env
```

### Edit `.env` with your values
```env
# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=urbancitiesadls2025
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Azure SQL Database
AZURE_SQL_SERVER=urban-cities-sql-srv-2025.database.windows.net
AZURE_SQL_DATABASE=urban_cities_db
AZURE_SQL_USERNAME=sqladmin
AZURE_SQL_PASSWORD=YourSecurePassword123!

# Alias variables (used by some scripts)
SQL_SERVER=urban-cities-sql-srv-2025.database.windows.net
SQL_DATABASE=urban_cities_db
SQL_USERNAME=sqladmin
SQL_PASSWORD=YourSecurePassword123!

# Azure Data Factory
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=urban-cities-rg
AZURE_DATA_FACTORY_NAME=urban-cities-adf
```

## Step 6: Create SQL Table

```powershell
cd ..\scripts\sql
python create_sql_table.py
```

Expected output: `✅ Table nyc_311_requests created successfully`

## Step 7: Create ADF Pipeline

```powershell
cd ..\adf
python create_adf_pipeline.py
```

Expected output: `✅ Pipeline CopyProcessedDataToSQL created successfully`

## Step 8: Start Airflow

```powershell
cd ..\..\astro-airflow
astro dev start
```

**This starts 5 Docker containers:**
- Scheduler
- Webserver
- Triggerer
- DAG Processor
- PostgreSQL database

**Wait for startup** (~2-3 minutes)

### Access Airflow UI
- URL: http://localhost:8080
- Username: `admin`
- Password: `admin`

## Step 9: Verify Setup

### Check DAG Exists
In Airflow UI, look for: `nyc_311_incremental_etl_azure`

### Trigger Manual Run
1. Click on the DAG name
2. Click "Play" button (top right)
3. Confirm trigger
4. Monitor task progress

### Expected Task Execution Order
1. `extract_nyc_311_data` (~30 seconds)
2. `transform_data` (~15 seconds)
3. `load_to_raw` (~20 seconds)
4. `load_to_processed` (~20 seconds)
5. `trigger_adf_pipeline` (~60 seconds)

## Step 10: Validate Data

### Check ADLS Files
```powershell
az storage blob list \
  --account-name urbancitiesadls2025 \
  --container-name processed \
  --output table
```

Expected: `nyc_311_processed.parquet` file

### Query SQL Database
Use Azure Data Studio, SSMS, or Azure Portal Query Editor:

```sql
-- Check record count
SELECT COUNT(*) FROM nyc_311_requests;

-- View sample data
SELECT TOP 10 * FROM nyc_311_requests ORDER BY created_date DESC;

-- Data quality summary
SELECT 
    COUNT(*) as total_records,
    AVG(data_quality_score) as avg_quality_score,
    COUNT(CASE WHEN status = 'Closed' THEN 1 END) as closed_count
FROM nyc_311_requests;
```

## Troubleshooting

### Terraform Errors

**"Storage account name not available"**
- Change `storage_account_name` in `terraform.tfvars` to a unique value
- Storage names must be globally unique across all Azure

**"SQL server name already exists"**
- Change `sql_server_name` in `terraform.tfvars`
- Server names must be globally unique

**"Insufficient permissions"**
- Ensure your Azure account has Contributor role on subscription
- Run: `az role assignment list --assignee {your-email}`

### Airflow Errors

**"Docker not running"**
- Start Docker Desktop
- Run: `docker ps` to verify

**"Port 8080 already in use"**
- Stop other services using port 8080
- Or change port in `astro-airflow/.astro/config.yaml`

**"DAG not appearing"**
- Wait 2-3 minutes for DAG processor to parse files
- Check logs: `astro dev logs`
- Verify DAG file syntax: `astro dev parse`

### Azure Connection Errors

**"Authentication failed"**
- Verify service principal credentials in `.env`
- Test login: 
  ```powershell
  az login --service-principal \
    -u $AZURE_CLIENT_ID \
    -p $AZURE_CLIENT_SECRET \
    --tenant $AZURE_TENANT_ID
  ```

**"Firewall blocking SQL connection"**
- Add your IP to SQL firewall rules in Azure Portal
- Or use Azure Cloud Shell to run queries

**"ADLS access denied"**
- Verify service principal has `Storage Blob Data Contributor` role
- Check role assignments:
  ```powershell
  az role assignment list --assignee {client-id}
  ```

## Next Steps

- Schedule: DAG is set to run hourly automatically
- Monitoring: Check Airflow UI for DAG runs
- Alerts: Configure email notifications in Airflow
- Documentation: See `docs/ARCHITECTURE.md` for technical details

## Clean Up

To remove all Azure resources:

```powershell
cd terraform
terraform destroy
```

⚠️ **Warning**: This deletes all data and cannot be undone!
