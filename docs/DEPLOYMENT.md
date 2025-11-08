# Production Deployment Guide

## Prerequisites

- Azure subscription with appropriate permissions
- Azure CLI installed and authenticated
- Terraform 1.5+
- Astronomer Astro CLI 1.38+
- Python 3.11+

## Infrastructure Setup

### 1. Deploy Azure Resources

```powershell
cd terraform

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Deploy infrastructure
terraform apply -auto-approve
```

**Deployed Resources:**
- Resource Group: `urban-cities-rg`
- Storage Account (ADLS Gen2): `urbancitiesadls2025`
- Data Factory: `urban-cities-adf`
- SQL Server: `urban-cities-sql-srv-2025`
- SQL Database: `urban_cities_db`

### 2. Create Service Principal

```bash
# Create service principal
az ad sp create-for-rbac --name urban-cities-sp --role Contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/urban-cities-rg

# Assign Storage Blob Data Contributor role
az role assignment create \
  --assignee {client-id} \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/{subscription-id}/resourceGroups/urban-cities-rg/providers/Microsoft.Storage/storageAccounts/urbancitiesadls2025
```

### 3. Configure Environment Variables

Create `.env` file in `astro-airflow/` directory:

```env
# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=urbancitiesadls2025
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Azure SQL
AZURE_SQL_SERVER=urban-cities-sql-srv-2025.database.windows.net
AZURE_SQL_DATABASE=urban_cities_db
AZURE_SQL_USERNAME=sqladmin
AZURE_SQL_PASSWORD=your-secure-password

# Azure Data Factory
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=urban-cities-rg
AZURE_DATA_FACTORY_NAME=urban-cities-adf
```

### 4. Create Azure Data Factory Pipeline

```powershell
cd scripts\adf
python create_adf_pipeline.py
```

This creates the `CopyProcessedDataToSQL` pipeline with:
- Source: ADLS processed container (Parquet)
- Sink: Azure SQL Database
- Mode: TRUNCATE and reload (prevents duplicates)

### 5. Start Airflow

```powershell
cd astro-airflow
astro dev start
```

Access Airflow UI: http://localhost:8080

## Validation

### Check Airflow

```bash
# View DAG status
astro dev run dags list

# Trigger manual run
astro dev run dags trigger nyc_311_incremental_etl_azure

# View logs
astro dev logs -f
```

### Verify Azure Storage

```bash
# List files in processed container
az storage blob list \
  --account-name urbancitiesadls2025 \
  --container-name processed \
  --output table
```

Expected files:
- `nyc_311_processed.parquet` - Master file with all data

### Check SQL Database

```sql
-- Connect to database
-- Server: urban-cities-sql-srv-2025.database.windows.net
-- Database: urban_cities_db

-- Verify data loaded
SELECT COUNT(*) as total_records FROM nyc_311_requests;

-- Check latest records
SELECT TOP 10 * FROM nyc_311_requests ORDER BY created_date DESC;

-- Data quality summary
SELECT 
    COUNT(*) as total_records,
    AVG(data_quality_score) as avg_quality,
    MIN(created_date) as earliest_record,
    MAX(created_date) as latest_record
FROM nyc_311_requests;
```

## Monitoring

### Airflow Metrics

Monitor in Airflow UI (http://localhost:8080):
- DAG success rate
- Task duration trends
- Failed tasks

### Azure Metrics

Check in Azure Portal:
- Data Factory pipeline runs
- Storage account capacity and transactions
- SQL Database DTU usage

### Log Locations

- **Airflow logs**: `astro-airflow/logs/`
- **DAG logs**: `astro-airflow/logs/dag_id=nyc_311_incremental_etl_azure/`
- **ETL state**: `astro-airflow/include/data/etl_state.json`

## Troubleshooting

### Airflow Issues

```bash
# Restart Airflow
astro dev restart

# View all container logs
docker logs astro-airflow-scheduler-1

# Reset environment
astro dev kill
astro dev start
```

### Azure Authentication Errors

```bash
# Test service principal
az login --service-principal \
  -u $AZURE_CLIENT_ID \
  -p $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID

# Verify permissions
az role assignment list --assignee $AZURE_CLIENT_ID
```

### SQL Connection Issues

- Add your IP to SQL firewall rules in Azure Portal
- Verify credentials in `.env` file
- Test connection using SQL Server Management Studio or Azure Data Studio

### Data Pipeline Failures

1. Check Airflow task logs for specific error
2. Verify API connectivity: `curl https://data.cityofnewyork.us/resource/erm2-nwe9.json?$limit=1`
3. Check ADLS connectivity and permissions
4. Verify ADF pipeline status in Azure Portal

## Scaling Considerations

### Increase ETL Frequency

Edit DAG schedule in `nyc_311_incremental_etl_azure.py`:

```python
schedule_interval="0 */4 * * *"  # Every 4 hours
# Or
schedule_interval="0 * * * *"    # Every hour
```

### Optimize SQL Performance

```sql
-- Add indexes for common queries
CREATE NONCLUSTERED INDEX IX_created_date 
ON nyc_311_requests(created_date);

CREATE NONCLUSTERED INDEX IX_agency_status 
ON nyc_311_requests(agency, status);
```

### Scale Azure Resources

- **SQL Database**: Upgrade to higher tier for more DTUs
- **Data Factory**: Configure parallel copy activities
- **Storage**: Enable lifecycle management for older data

## Backup and Recovery

### Database Backups

Azure SQL Database has automatic backups enabled:
- Point-in-time restore: 7 days
- Long-term retention: Configure in Azure Portal

### Storage Backups

Enable soft delete on ADLS:

```bash
az storage account blob-service-properties update \
  --account-name urbancitiesadls2025 \
  --enable-delete-retention true \
  --delete-retention-days 7
```

### ETL State Backup

The ETL state is stored in `etl_state.json`. Back this up regularly:

```bash
# Backup state file
cp astro-airflow/include/data/etl_state.json etl_state_backup_$(date +%Y%m%d).json
```

## Security Hardening

### Production Checklist

- [ ] Use Azure Key Vault for secrets instead of `.env` file
- [ ] Enable Azure SQL Database auditing
- [ ] Configure Azure Private Link for ADLS and SQL
- [ ] Enable diagnostic logging on all Azure resources
- [ ] Use managed identities instead of service principals where possible
- [ ] Implement network security groups and firewall rules
- [ ] Enable Azure Defender for SQL
- [ ] Rotate service principal secrets regularly
- [ ] Use separate resource groups for dev/staging/production

### Recommended Configuration

```bash
# Enable Azure SQL auditing
az sql server audit-policy update \
  --resource-group urban-cities-rg \
  --server urban-cities-sql-srv-2025 \
  --state Enabled \
  --storage-account urbancitiesadls2025

# Enable diagnostic logs for Data Factory
az monitor diagnostic-settings create \
  --resource {data-factory-resource-id} \
  --name adf-diagnostics \
  --logs '[{"category":"ActivityRuns","enabled":true}]' \
  --workspace {log-analytics-workspace-id}
```
