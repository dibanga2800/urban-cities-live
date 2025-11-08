# NYC 311 Service Requests ETL Pipeline

A production data pipeline that extracts NYC 311 service request data, transforms it with quality checks, and loads it into Azure SQL Database for analytics.

## Features

- **Incremental Loading**: Processes only new records since last successful run
- **Automatic Deduplication**: Single master files with built-in duplicate removal
- **Data Quality Scoring**: Every record scored 0-100 based on completeness
- **Automated Schedule**: Runs hourly via Apache Airflow
- **Infrastructure as Code**: Complete Azure deployment via Terraform

## Architecture

```
NYC 311 API → Airflow ETL → Azure Data Lake Gen2 → Azure Data Factory → Azure SQL Database
```

**Data Flow:**
1. **Extract**: Incremental pull from NYC 311 API using SoQL queries
2. **Transform**: Data cleaning, quality scoring, feature engineering
3. **Load to ADLS**: Append to master files (nyc_311_raw.csv, nyc_311_processed.parquet)
4. **Copy to SQL**: ADF pipeline truncates and reloads SQL table

## Technology Stack

- **Orchestration**: Apache Airflow (Astronomer Astro Runtime 3.1-3)
- **Cloud**: Azure Data Lake Gen2, Azure Data Factory, Azure SQL Database
- **Infrastructure**: Terraform
- **Languages**: Python 3.12, SQL

## Quick Start

### Prerequisites

- Azure CLI and active subscription
- Terraform 1.5+
- Astronomer Astro CLI 1.38+
- Python 3.11+

### Deploy Infrastructure

```powershell
# 1. Clone and navigate
git clone <repo-url>
cd Urban_Cities_live_Service

# 2. Login to Azure
az login

# 3. Configure Terraform variables
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 4. Deploy Azure resources
terraform init
terraform apply -auto-approve

# 5. Create ADF pipeline
cd ..\scripts\adf
python create_adf_pipeline.py

# 6. Start Airflow
cd ..\..\astro-airflow
astro dev start

# 7. Access Airflow UI at http://localhost:8080
```

## Project Structure

```
Urban_Cities_live_Service/
├── astro-airflow/           # Airflow DAGs and configuration
│   ├── dags/
│   │   └── nyc_311_incremental_etl_azure.py
│   └── include/
│       ├── Extraction.py
│       ├── Transformation.py
│       └── Loading_Azure.py
├── terraform/               # Infrastructure as Code
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── scripts/                 # Utility scripts
│   ├── adf/create_adf_pipeline.py
│   └── sql/create_sql_table.py
└── docs/                    # Documentation
```

## Configuration

### Environment Variables

Create a `.env` file in the `astro-airflow` directory:

```env
# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret

# Azure SQL
AZURE_SQL_SERVER=your_server.database.windows.net
AZURE_SQL_DATABASE=urban_cities_db
AZURE_SQL_USERNAME=sqladmin
AZURE_SQL_PASSWORD=your_password

# Azure Data Factory
AZURE_SUBSCRIPTION_ID=your_subscription_id
AZURE_RESOURCE_GROUP=urban-cities-rg
AZURE_DATA_FACTORY_NAME=urban-cities-adf

# ETL Configuration
FORCE_FULL_LOAD=false          # Set to 'true' for initial full historical load
HISTORICAL_DAYS_BACK=30        # Number of days to load when FORCE_FULL_LOAD=true
```

### Terraform Variables

Required variables in `terraform.tfvars`:

```hcl
resource_group_name  = "urban-cities-rg"
location             = "eastus"
storage_account_name = "urbancitiesadls2025"
sql_admin_password   = "YourSecurePassword123!"
```

## DAG Details

**Name**: `nyc_311_incremental_etl_azure`  
**Schedule**: `0 * * * *` (hourly)  
**Tasks**:
1. `extract_nyc_311_data` - Pull new records from API
2. `transform_data` - Clean and enrich data
3. `load_to_raw` - Upload raw CSV to ADLS
4. `load_to_processed` - Upload processed Parquet to ADLS
5. `create_sql_table` - Create SQL table if not exists (automated)
6. `trigger_adf_pipeline` - Copy data to SQL via ADF
7. `update_etl_state` - Update timestamp for incremental loads

**Initial Setup**: For first deployment, set `FORCE_FULL_LOAD=true` in `.env` to load historical data (default 30 days). After initial load, set to `false` for incremental hourly updates.

## Data Schema

**SQL Table**: `nyc_311_requests` (20 columns)

Key columns:
- `unique_key` - Primary key (hash of request details)
- `created_date` - Request timestamp
- `agency`, `complaint_type`, `descriptor` - Request classification
- `borough`, `latitude`, `longitude` - Location
- `status`, `closed_date` - Resolution tracking
- `resolution_time_hours` - Derived metric
- `data_quality_score` - Completeness score (0-100)

## Monitoring

### Check Airflow DAG Status
```bash
# View recent DAG runs
astro dev run dags list-runs -d nyc_311_incremental_etl_azure

# Check task logs
astro dev logs
```

### Query SQL Data
```sql
-- Total requests
SELECT COUNT(*) FROM nyc_311_requests;

-- Recent requests
SELECT TOP 10 * FROM nyc_311_requests 
ORDER BY created_date DESC;

-- Average quality score
SELECT AVG(data_quality_score) as avg_quality 
FROM nyc_311_requests;
```

### Check ADLS Files
```bash
# Using Azure CLI
az storage blob list \
  --account-name urbancitiesadls2025 \
  --container-name processed \
  --output table
```

## Troubleshooting

### Airflow Container Issues
```bash
# Restart Airflow
astro dev restart

# View logs
astro dev logs -f

# Reset environment
astro dev kill
astro dev start
```

### Azure Authentication Errors
```bash
# Verify Service Principal
az login --service-principal \
  -u $AZURE_CLIENT_ID \
  -p $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID

# Check permissions
az role assignment list --assignee $AZURE_CLIENT_ID
```

### SQL Connection Issues
- Ensure firewall rules allow your IP
- Verify credentials in `.env` file
- Check SQL server status in Azure Portal

## Production Deployment

See `docs/PRODUCTION_BUILD.md` for detailed production deployment guide including:
- Security hardening
- Monitoring setup
- Backup configuration
- Scaling considerations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

[Your License Here]

## Contact

[Your Contact Information]
