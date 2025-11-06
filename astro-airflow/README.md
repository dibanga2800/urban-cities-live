# NYC 311 ETL Pipeline - Astronomer Astro

## Overview

This is an Airflow project running on Astronomer Astro Runtime for processing NYC 311 service request data. The pipeline extracts data from the NYC Open Data API, transforms it, loads to Azure Data Lake Storage (ADLS), and triggers Azure Data Factory (ADF) to copy processed data to Azure SQL Database.

## Table of Contents

- [Installation Steps](#installation-steps)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Running the Pipeline](#running-the-pipeline)
- [Astro Commands Reference](#astro-commands-reference)
- [DAG Details](#dag-details)
- [Troubleshooting](#troubleshooting)

---

## Installation Steps

### Prerequisites

- **Windows 10/11** with PowerShell
- **Docker Desktop** or **Podman** installed and running
- **winget** (Windows Package Manager) installed
- **Azure Account** with Service Principal credentials

### Step 1: Install Astronomer Astro CLI

```powershell
# Install Astro CLI via winget (will also install Podman if needed)
winget install -e --id Astronomer.Astro

# Verify installation
astro version
```

**Note**: If `astro` command is not recognized, restart your PowerShell terminal or use the full path:
```powershell
& "C:\Users\<YourUsername>\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe\astro.exe" version
```

### Step 2: Navigate to Project Directory

```powershell
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\astro-airflow"
```

### Step 3: Configure Environment Variables

Edit the `.env` file with your credentials:

```bash
# NYC 311 API Configuration
NYC_311_API_URL=https://data.cityofnewyork.us/resource/erm2-nwe9.json
NYC_APP_TOKEN=your_app_token_here
BATCH_SIZE=1000

# Azure Service Principal
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
AZURE_SUBSCRIPTION_ID=your_subscription_id

# Azure Data Lake Storage
ADLS_ACCOUNT_NAME=your_storage_account_name

# Azure Data Factory
ADF_NAME=your_data_factory_name
ADF_RESOURCE_GROUP=your_resource_group

# Azure SQL Database
SQL_SERVER=your_server.database.windows.net
SQL_DATABASE=your_database_name
SQL_USERNAME=your_username
SQL_PASSWORD=your_password
```

### Step 4: Start Airflow

```powershell
# Start all Airflow services (first run takes 3-5 minutes)
astro dev start

# Or with full path:
& "C:\Users\David Ibanga\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe\astro.exe" dev start
```

**What happens during startup:**
1. Builds Docker image with Astro Runtime 3.1-3
2. Installs Python dependencies from `requirements.txt`
3. Initializes PostgreSQL database
4. Starts 5 containers: Postgres, Scheduler, DAG Processor, API Server, Triggerer
5. Opens browser to http://localhost:8080

### Step 5: Access Airflow UI

- **URL**: http://localhost:8080
- **Username**: `admin`
- **Password**: `admin`

---

## Project Structure

```
astro-airflow/
├── .astro/                          # Astro CLI configuration (auto-generated)
├── dags/                            # Airflow DAG definitions
│   ├── nyc_311_incremental_etl_azure.py   # Main ETL pipeline DAG
│   ├── Transformation.py            # DAG-specific transformation logic
│   └── __pycache__/                 # Python cache files
├── include/                         # Shared Python modules
│   ├── Extraction.py                # Data extraction from NYC 311 API
│   ├── Transformation.py            # Data cleaning and transformation
│   ├── Loading_Azure.py             # Azure ADLS and ADF integration
│   └── data/
│       └── etl_state.json           # Tracks last processed timestamp
├── plugins/                         # Custom Airflow plugins (optional)
├── tests/                           # DAG unit tests
│   └── dags/
│       └── test_dag_example.py      # Example test file
├── .dockerignore                    # Files to exclude from Docker build
├── .env                             # Environment variables (not in git)
├── .gitignore                       # Git ignore rules
├── airflow_settings.yaml            # Local Airflow connections/variables
├── Dockerfile                       # Astro Runtime base image
├── packages.txt                     # OS-level packages (apt-get)
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── MIGRATION_NOTES.md               # Docker Compose to Astro migration details
└── QUICK_START.md                   # Quick reference guide
```

### Key Directories

- **`dags/`**: Place all DAG Python files here. Airflow automatically scans this directory.
- **`include/`**: Shared code (classes, functions, utilities) used by multiple DAGs. Automatically added to Python path.
- **`plugins/`**: Custom Airflow operators, hooks, sensors, or UI modifications.
- **`tests/`**: pytest-compatible tests for your DAGs.

---

## Configuration

### Python Dependencies (`requirements.txt`)

```txt
# Core dependencies
pandas>=1.5.0
requests>=2.28.0
python-dotenv>=0.19.0
numpy>=1.21.0

# Azure dependencies
azure-storage-file-datalake>=12.8.0
azure-identity>=1.12.0
azure-mgmt-datafactory>=3.0.0
azure-mgmt-resource>=23.0.0
pyodbc>=4.0.39

# Airflow providers
apache-airflow-providers-postgres>=5.6.0

# Development tools
pytest>=7.0.0
black>=22.0.0
flake8>=4.0.0
```

**Note**: sqlalchemy version is managed by Astro Runtime. Do not specify explicit version to avoid conflicts.

### Dockerfile

```dockerfile
FROM astrocrpublic.azurecr.io/runtime:3.1-3
```

Astro Runtime 3.1-3 includes:
- Apache Airflow 2.10.x
- Python 3.11
- Pre-installed provider packages
- Optimized for production use

### Environment Variables (`.env`)

Key variables used by the pipeline:
- **NYC_311_API_URL**: NYC Open Data API endpoint
- **NYC_APP_TOKEN**: API authentication token
- **AZURE_CLIENT_ID**: Service Principal application ID
- **AZURE_CLIENT_SECRET**: Service Principal password
- **ADLS_ACCOUNT_NAME**: Azure Data Lake Storage account
- **ADF_NAME**: Azure Data Factory name
- **SQL_SERVER**: Azure SQL Server FQDN

---

## Running the Pipeline

### Start Airflow Environment

```powershell
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\astro-airflow"
astro dev start
```

### Verify DAG is Loaded

1. Open http://localhost:8080
2. Login with `admin` / `admin`
3. Find DAG: `nyc_311_incremental_etl_azure`
4. Check for any import errors (red banner)

### Trigger DAG Manually

**Via UI:**
1. Click on DAG name
2. Click play button (▶) on top right
3. Click "Trigger DAG"
4. Monitor task execution in Graph view

**Via CLI:**
```powershell
# Run a specific DAG
astro dev run dags trigger nyc_311_incremental_etl_azure

# List all DAGs
astro dev run dags list

# Test a specific task
astro dev run tasks test nyc_311_incremental_etl_azure extract_data 2024-11-05
```

### Monitor Logs

**View all logs:**
```powershell
astro dev logs
```

**View specific service logs:**
```powershell
astro dev logs -s webserver
astro dev logs -s scheduler
astro dev logs -s triggerer
```

**Follow logs in real-time:**
```powershell
astro dev logs -f
```

### Stop Airflow

```powershell
# Stop all services (data preserved)
astro dev stop

# Stop and remove volumes (clean slate)
astro dev kill
```

### Restart After Code Changes

```powershell
# Restart all services
astro dev restart

# Or stop and start
astro dev stop
astro dev start
```

---

## Astro Commands Reference

### Development Commands

| Command | Description |
|---------|-------------|
| `astro dev start` | Start Airflow locally |
| `astro dev stop` | Stop Airflow (preserves data) |
| `astro dev restart` | Restart all services |
| `astro dev kill` | Stop and remove all data |
| `astro dev logs` | View logs from all services |
| `astro dev logs -f` | Follow logs in real-time |
| `astro dev ps` | List running containers |
| `astro dev run <command>` | Run Airflow CLI command |
| `astro dev pytest` | Run DAG tests |
| `astro dev bash` | Open bash shell in scheduler |
| `astro dev python` | Open Python REPL |

### Airflow CLI via Astro

```powershell
# List DAGs
astro dev run dags list

# Trigger a DAG
astro dev run dags trigger nyc_311_incremental_etl_azure

# Test a task
astro dev run tasks test nyc_311_incremental_etl_azure extract_data 2024-11-05

# List connections
astro dev run connections list

# Create connection
astro dev run connections add my_conn --conn-type http --conn-host example.com
```

### Testing Commands

```powershell
# Run all tests
astro dev pytest

# Run specific test file
astro dev pytest tests/dags/test_dag_example.py

# Run with verbose output
astro dev pytest -v
```

### Deployment Commands (Astro Cloud)

```powershell
# Login to Astronomer
astro login

# List deployments
astro deployment list

# Deploy to production
astro deploy

# View deployment logs
astro deployment logs
```

---

## DAG Details

### NYC 311 Incremental ETL Pipeline

**DAG ID**: `nyc_311_incremental_etl_azure`

**Schedule**: Every 15 minutes

**Tasks**:
1. **start** - Dummy start task
2. **extract_data** - Fetch data from NYC 311 API (incremental based on state file)
3. **transform_data** - Clean, validate, and enrich data
4. **load_to_azure** - Upload raw and processed data to ADLS
5. **trigger_adf_pipeline** - Trigger Azure Data Factory to copy data to SQL Database
6. **update_state** - Save last processed timestamp
7. **cleanup_temp_files** - Remove temporary CSV files
8. **send_notification** - Log completion metrics
9. **end** - Dummy end task

**Flow**:
```
start → extract_data → transform_data → load_to_azure → trigger_adf_pipeline 
      → update_state → cleanup_temp_files → send_notification → end
```

**State Management**:
- State file: `/usr/local/airflow/include/data/etl_state.json`
- Tracks: `last_processed_time` for incremental extraction
- Updates: After each successful run

**Azure Integration**:
- **Extraction**: NYC Open Data API
- **Storage**: ADLS Gen2 (raw & processed containers)
- **Processing**: Azure Data Factory pipeline
- **Database**: Azure SQL Database

---

## Troubleshooting

### Issue: `astro` command not recognized

**Solution 1**: Restart PowerShell terminal to refresh PATH

**Solution 2**: Use full path:
```powershell
& "C:\Users\<YourUsername>\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe\astro.exe" dev start
```

**Solution 3**: Add to PATH permanently:
```powershell
$astroPath = "C:\Users\<YourUsername>\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe"
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$astroPath", "User")
```

### Issue: Port 8080 already in use

**Check what's using the port:**
```powershell
netstat -ano | findstr :8080
```

**Stop conflicting services:**
```powershell
# Stop old Docker Compose Airflow
docker-compose -f docker-compose-airflow.yml down

# Or change Astro port in .env
AIRFLOW__WEBSERVER__WEB_SERVER_PORT=8081
```

### Issue: DAG import errors

**Check logs:**
```powershell
astro dev logs -s scheduler | Select-String "ERROR"
```

**Common causes:**
- Missing Python packages in `requirements.txt`
- Incorrect import paths (should be `from include.Module import...`)
- Syntax errors in DAG file

**Validate DAG syntax:**
```powershell
astro dev run dags list-import-errors
```

### Issue: Docker/Podman not running

**Error**: `Error response from daemon: Bad response from Docker engine`

**Solution**: Start Docker Desktop or Podman
```powershell
# Check Docker/Podman status
docker ps

# If not running, start Docker Desktop from Start Menu
```

### Issue: Azure authentication fails

**Error**: `ClientAuthenticationError` or `ServicePrincipalCredential authentication failed`

**Check**:
1. `.env` file exists in project root
2. `AZURE_CLIENT_ID` is correct (27b470a2-fa5d-458a-85d5-e639c0791f23)
3. `AZURE_CLIENT_SECRET` is valid (secrets expire)
4. Service Principal has correct permissions:
   - Storage Blob Data Contributor on ADLS
   - Contributor on Data Factory
   - SQL Database access

**Test credentials:**
```powershell
az login --service-principal -u <CLIENT_ID> -p <CLIENT_SECRET> --tenant <TENANT_ID>
```

### Issue: State file not found

**Error**: `FileNotFoundError: etl_state.json`

**Solution**: Create state file in container:
```powershell
astro dev bash
mkdir -p /usr/local/airflow/include/data
echo '{"last_processed_time": "2025-10-31T00:00:00", "updated_at": "2025-11-05T00:00:00"}' > /usr/local/airflow/include/data/etl_state.json
exit
```

### Issue: Slow build times

**First build**: 3-5 minutes (normal)
**Subsequent builds**: Should be < 30 seconds (Docker caching)

**If builds are always slow:**
```powershell
# Clean Docker cache
docker system prune -a

# Rebuild from scratch
astro dev kill
astro dev start
```

### Issue: Memory or performance issues

**Increase Docker resources:**
- Docker Desktop → Settings → Resources
- Increase CPU: 4 cores minimum
- Increase Memory: 8GB minimum

---

## Additional Resources

- **Astro Documentation**: https://www.astronomer.io/docs/astro/
- **Airflow Documentation**: https://airflow.apache.org/docs/
- **NYC 311 API**: https://data.cityofnewyork.us/
- **Azure SDK for Python**: https://learn.microsoft.com/python/api/overview/azure/

---

## Support

For issues with:
- **Astro CLI**: https://www.astronomer.io/docs/astro/cli/troubleshoot-locally
- **Azure Integration**: Check Azure Portal for resource status
- **DAG Development**: Review Airflow logs and task instances

---

## Next Steps

1. ✅ Install Astro CLI
2. ✅ Configure `.env` file
3. ✅ Start Airflow: `astro dev start`
4. ⏳ Access UI: http://localhost:8080
5. ⏳ Trigger DAG manually
6. ⏳ Monitor execution
7. ⏳ Deploy to Astro Cloud (optional)
