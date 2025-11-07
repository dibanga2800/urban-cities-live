# Azure ETL Integration Setup Guide

Complete guide for integrating your NYC 311 ETL pipeline with Azure infrastructure.

## 🎯 Architecture Overview

```
NYC 311 API
    ↓ (Extract)
Extraction.py
    ↓
Raw Data (DataFrame)
    ↓
    ├─→ ADLS Gen2 / raw container (CSV)
    ↓
Transformation.py
    ↓
Processed Data (DataFrame)
    ↓
    ├─→ ADLS Gen2 / processed container (CSV)
    ↓
Azure Data Factory Pipeline (triggered)
    ↓
Azure SQL Database (final destination)
```

## 📋 Prerequisites

1. **Terraform Infrastructure Deployed** ✅
   - ADLS Gen2 Storage Account: `urbancitiesadls2025`
   - Containers: `raw`, `processed`, `curated`
   - Azure Data Factory: `urban-cities-adf`
   - Azure SQL Database: `urban_cities_db`

2. **Python Environment**
   - Python 3.8+
   - Virtual environment (recommended)

3. **Azure Authentication**
   - Azure CLI logged in, OR
   - Service Principal credentials

---

## 🚀 Setup Instructions

### Step 1: Get Azure Credentials

```powershell
# Navigate to terraform directory
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\terraform"

# Get Storage Account Key
terraform output -raw storage_account_primary_access_key

# Copy this value - you'll need it for .env file
```

### Step 2: Configure Environment Variables

```powershell
# Navigate to notebook directory
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\notebook"

# Copy example env file
cp .env.example .env

# Edit with your values
code .env
```

**Update `.env` with:**

```bash
# Azure Data Lake Storage Gen2
ADLS_ACCOUNT_NAME=urbancitiesadls2025
ADLS_ACCOUNT_KEY=<paste_storage_key_from_terraform_output>

# Azure Data Factory
ADF_NAME=urban-cities-adf
ADF_RESOURCE_GROUP=urban-cities-rg

# Azure Subscription
AZURE_SUBSCRIPTION_ID=12f0f306-0cdf-41a6-9028-a7757690a1e2
AZURE_TENANT_ID=edc41ca9-a02a-4623-97cb-2a58f19e3c46

# Azure SQL Database
SQL_SERVER=urban-cities-sql-server.database.windows.net
SQL_DATABASE=urban_cities_db
SQL_USERNAME=sqladmin
SQL_PASSWORD=<your_password_from_terraform_tfvars>

# NYC 311 API
NYC_311_API_URL=https://data.cityofnewyork.us/resource/erm2-nwe9.json
NYC_APP_TOKEN=<optional_your_nyc_api_token>
```

### Step 3: Install Python Dependencies

```powershell
# Create virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### Step 4: Test Azure Connection

```powershell
# Test the new Azure loader
python Loading_Azure.py
```

Expected output:
```
Using storage account key authentication
Testing raw data upload...
Successfully uploaded 3 records to raw container: raw-data/test_raw_20251104_120000.csv
Raw upload result: abfss://raw@urbancitiesadls2025.dfs.core.windows.net/...

Testing processed data upload...
Successfully uploaded 3 records to processed container: processed-data/test_processed_20251104_120000.csv
...
```

### Step 5: Create Azure Data Factory Pipeline

#### Option A: Using Azure Portal (Recommended for first time)

1. **Open Azure Portal**: https://portal.azure.com
2. **Navigate to Data Factory**: `urban-cities-adf`
3. **Click "Author & Monitor"**
4. **Create New Pipeline**: Name it `CopyProcessedToSQL`

5. **Add Copy Activity**:
   - Source: ADLS Gen2 / processed container
   - Sink: Azure SQL Database / urban_cities_db
   
6. **Configure Source**:
   - Linked Service: Create new ADLS Gen2 linked service
   - Account: `urbancitiesadls2025`
   - Container: `processed`
   - File format: CSV with headers

7. **Configure Sink**:
   - Linked Service: Create new Azure SQL Database linked service
   - Server: `urban-cities-sql-server.database.windows.net`
   - Database: `urban_cities_db`
   - Table: Create table named `nyc_311_requests`
   
8. **Add Parameters**:
   - `sourceFilePath` (string) - Path to source CSV file
   
9. **Test Pipeline**: Use "Debug" to test

10. **Publish**: Click "Publish All"

#### Option B: Using Azure CLI (Advanced)

```powershell
# Create ADF linked services and pipeline via CLI
# (See ADF_PIPELINE_SETUP.md for detailed commands)
```

### Step 6: Create SQL Database Table

```powershell
# Connect to SQL Database and create table
# Using Azure Data Studio or SSMS
```

```sql
CREATE TABLE nyc_311_requests (
    unique_key BIGINT PRIMARY KEY,
    created_date DATETIME,
    closed_date DATETIME,
    agency VARCHAR(100),
    agency_name VARCHAR(255),
    complaint_type VARCHAR(255),
    descriptor VARCHAR(255),
    location_type VARCHAR(255),
    incident_zip VARCHAR(10),
    incident_address VARCHAR(500),
    street_name VARCHAR(255),
    city VARCHAR(100),
    borough VARCHAR(50),
    latitude FLOAT,
    longitude FLOAT,
    location VARCHAR(255),
    status VARCHAR(50),
    resolution_description VARCHAR(MAX),
    processed_at DATETIME DEFAULT GETDATE()
);

CREATE INDEX idx_created_date ON nyc_311_requests(created_date);
CREATE INDEX idx_complaint_type ON nyc_311_requests(complaint_type);
CREATE INDEX idx_borough ON nyc_311_requests(borough);
```

---

## 🐳 Running with Docker/Airflow

### Step 1: Update Docker Compose

The `docker-compose.yml` already includes environment variables for Azure.

### Step 2: Start Airflow

```powershell
# Navigate to notebook directory
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\notebook"

# Ensure Docker is running
docker --version

# Start Airflow
docker-compose up -d

# Check status
docker-compose ps
```

### Step 3: Access Airflow UI

1. Open browser: http://localhost:8080
2. Login: `admin` / `admin`
3. Enable DAG: `nyc_311_incremental_etl_azure`

### Step 4: Monitor Pipeline

- View DAG runs in Airflow UI
- Check ADLS containers in Azure Portal
- Monitor ADF pipeline runs
- Query SQL Database for loaded data

---

## 📊 Pipeline Flow

### Task 1: Extract Data
- Fetches data from NYC 311 API
- Incremental loading based on last processed timestamp
- Saves raw data temporarily

### Task 2: Transform Data
- Cleans and validates data
- Standardizes formats
- Calculates quality metrics
- Saves processed data temporarily

### Task 3: Load to Azure
- Uploads raw data to ADLS `raw` container
- Uploads processed data to ADLS `processed` container
- Returns paths for next task

### Task 4: Trigger ADF Pipeline
- Triggers Azure Data Factory pipeline
- Passes processed file path as parameter
- Waits for pipeline completion
- Returns run status

### Task 5: Update State
- Updates last processed timestamp
- Saves state for next incremental run

### Task 6: Cleanup
- Removes temporary files
- Frees up disk space

### Task 7: Notify
- Sends completion notification
- Logs metrics and status

---

## 🔍 Testing

### Test Individual Components

```powershell
# Test extraction
python Extraction.py

# Test transformation
python Transformation.py

# Test Azure loading
python Loading_Azure.py
```

### Test Complete Pipeline (without Airflow)

```powershell
# Run manual ETL
python test_pipeline.py
```

### Test with Airflow

1. Trigger DAG manually in Airflow UI
2. Monitor task execution
3. Check logs for each task
4. Verify data in ADLS and SQL

---

## 📁 Data Flow Example

### 1. Raw Data in ADLS (`raw` container)
```
raw-data/
  ├── nyc_311_raw_20251104_120000.csv  (1000 records)
  ├── nyc_311_raw_20251104_121500.csv  (850 records)
  └── nyc_311_raw_20251104_123000.csv  (920 records)
```

### 2. Processed Data in ADLS (`processed` container)
```
processed-data/
  ├── nyc_311_processed_20251104_120000.csv  (995 records - 5 invalid removed)
  ├── nyc_311_processed_20251104_121500.csv  (845 records)
  └── nyc_311_processed_20251104_123000.csv  (918 records)
```

### 3. Data in SQL Database
```sql
SELECT COUNT(*) FROM nyc_311_requests;
-- Result: 2758 (cumulative from all loads)

SELECT TOP 10 * FROM nyc_311_requests 
ORDER BY created_date DESC;
```

---

## 🔒 Security Best Practices

### 1. Service Principal (Production)

Create a dedicated service principal for ETL:

```powershell
# Create service principal
az ad sp create-for-rbac `
  --name "urban-cities-etl" `
  --role Contributor `
  --scopes /subscriptions/12f0f306-0cdf-41a6-9028-a7757690a1e2/resourceGroups/urban-cities-rg

# Output:
# {
#   "appId": "xxx",  <- AZURE_CLIENT_ID
#   "password": "yyy",  <- AZURE_CLIENT_SECRET
#   "tenant": "edc41ca9-a02a-4623-97cb-2a58f19e3c46"
# }

# Add to .env file
```

### 2. Managed Identity (Recommended)

Use Azure VM or Container Instances with managed identity - no credentials needed!

### 3. Azure Key Vault

Store secrets in Key Vault:

```powershell
# Create Key Vault
az keyvault create --name "urban-cities-kv" --resource-group "urban-cities-rg"

# Store secrets
az keyvault secret set --vault-name "urban-cities-kv" --name "storage-key" --value "<key>"
az keyvault secret set --vault-name "urban-cities-kv" --name "sql-password" --value "<password>"

# Update code to fetch from Key Vault
```

---

## 🐛 Troubleshooting

### Issue: "DefaultAzureCredential failed to retrieve token"

**Solution**: Ensure you're logged in with Azure CLI:
```powershell
az login
az account show
```

### Issue: "BlobNotFound" in ADLS

**Solution**: Verify container names:
```powershell
az storage container list --account-name urbancitiesadls2025
```

### Issue: ADF Pipeline not found

**Solution**: Create the pipeline in Azure Portal first (see Step 5 above)

### Issue: SQL Connection Failed

**Solution**: Check firewall rules:
```powershell
# Get your IP
$myIP = (Invoke-WebRequest -Uri "https://api.ipify.org").Content

# Add firewall rule
az sql server firewall-rule create `
  --resource-group urban-cities-rg `
  --server urban-cities-sql-server `
  --name AllowMyIP `
  --start-ip-address $myIP `
  --end-ip-address $myIP
```

### Issue: Permission Denied

**Solution**: Grant proper RBAC roles:
```powershell
# Storage Blob Data Contributor
az role assignment create `
  --assignee <your-email-or-sp-id> `
  --role "Storage Blob Data Contributor" `
  --scope /subscriptions/12f0f306-0cdf-41a6-9028-a7757690a1e2/resourceGroups/urban-cities-rg/providers/Microsoft.Storage/storageAccounts/urbancitiesadls2025
```

---

## 📚 Additional Resources

- [Azure Data Lake Storage Gen2 Docs](https://docs.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-introduction)
- [Azure Data Factory Docs](https://docs.microsoft.com/en-us/azure/data-factory/)
- [Azure SQL Database Docs](https://docs.microsoft.com/en-us/azure/azure-sql/)
- [Apache Airflow Docs](https://airflow.apache.org/docs/)

---

## 📞 Quick Commands Reference

```powershell
# Get Storage Key
terraform output -raw storage_account_primary_access_key

# Test Azure Connection
python Loading_Azure.py

# Start Airflow
docker-compose up -d

# View Airflow Logs
docker-compose logs -f airflow-scheduler

# Stop Airflow
docker-compose down

# Access Airflow
http://localhost:8080

# Query SQL Database
# Use Azure Data Studio or SSMS
# Server: urban-cities-sql-server.database.windows.net
# Database: urban_cities_db
```

---

**Last Updated:** November 4, 2025  
**Status:** ✅ Ready for Production
