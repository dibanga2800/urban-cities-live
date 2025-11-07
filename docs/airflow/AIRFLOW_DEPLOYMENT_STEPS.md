# Airflow DAG Deployment & Testing Guide

## ✅ What's Ready

Your Airflow DAG (`nyc_311_incremental_etl_azure.py`) has been **updated** with:
- ✅ Extract from NYC 311 API
- ✅ Transform data with quality metrics
- ✅ Load to ADLS raw container
- ✅ Load to ADLS processed container
- ✅ **Trigger ADF pipeline** (`CopyProcessedDataToSQL`) - **NEWLY UPDATED**
- ✅ Update ETL state tracking
- ✅ Cleanup temporary files
- ✅ Send completion notification

## 🚀 Quick Start Guide

### Step 1: Start Docker Desktop
1. Open Docker Desktop application
2. Wait for Docker to fully start (whale icon in system tray)
3. Verify: `docker ps` should work without errors

### Step 2: Start Airflow
```powershell
# Navigate to project directory
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\notebook"

# Start Airflow with Docker Compose
docker-compose up -d

# Check if containers are running
docker ps
```

You should see containers like:
- `airflow-webserver`
- `airflow-scheduler`
- `airflow-worker`
- `postgres` (for Airflow metadata)
- `redis` (for task queue)

### Step 3: Access Airflow UI
1. Open browser: http://localhost:8080
2. Login credentials:
   - Username: `admin`
   - Password: `admin` (or check your docker-compose.yml)

### Step 4: Verify DAG is Loaded
1. In Airflow UI, look for DAG: `nyc_311_incremental_etl_azure`
2. Check if all 7 tasks are visible:
   - `start` → `extract_data` → `transform_data` → `load_to_azure` → `trigger_adf_pipeline` → `update_state` → `cleanup_temp_files` → `send_notification` → `end`

### Step 5: Test the DAG

#### Option A: Manual Trigger (Recommended for First Test)
1. Click on the DAG name: `nyc_311_incremental_etl_azure`
2. Click the **▶ Play** button (Trigger DAG)
3. Monitor the task execution in real-time
4. Check logs for each task

#### Option B: Enable Scheduled Runs
1. Toggle the DAG switch to **ON** (currently set to run every 15 minutes)
2. Wait for the next scheduled run
3. Monitor execution

### Step 6: Monitor Execution

#### Watch Live Progress
```bash
# Follow scheduler logs
docker logs -f airflow-scheduler

# Follow webserver logs
docker logs -f airflow-webserver

# Follow worker logs
docker logs -f airflow-worker
```

#### Check Task Logs in UI
1. Click on the DAG run (colored square)
2. Click on individual task boxes
3. View logs for each task

### Step 7: Verify End-to-End Success

After a successful run, verify:

1. **Data in ADLS**:
   - Go to Azure Portal → Storage Account → `urbancitiesadls2025`
   - Check `raw` container → `raw-data` folder for new files
   - Check `processed` container → `processed-data` folder for new files

2. **ADF Pipeline Execution**:
   - Go to Azure Portal → Data Factory → `urban-cities-adf`
   - Check "Monitor" section for recent pipeline runs
   - Run ID should match the one in Airflow logs

3. **Data in SQL Database**:
   ```powershell
   python verify_sql_data.py
   ```
   Should show new records with recent timestamps

## 🔧 Configuration Files

### Environment Variables (in Docker Compose or .env)
Make sure these are set:
```bash
# NYC 311 API
NYC_311_API_URL=https://data.cityofnewyork.us/resource/erm2-nwe9.json
NYC_APP_TOKEN=your_token_here

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=urbancitiesadls2025
AZURE_TENANT_ID=edc41ca9-a02a-4623-97cb-2a58f19e3c46
AZURE_CLIENT_ID=27b470a2-fa5d-458a-85d5-e639c0791f23
AZURE_CLIENT_SECRET=your_secret_here
AZURE_SUBSCRIPTION_ID=12f0f306-0cdf-41a6-9028-a7757690a1e2
AZURE_RESOURCE_GROUP=urban-cities-rg

# Azure Data Factory
ADF_NAME=urban-cities-adf

# SQL Database (if needed)
SQL_SERVER=urban-cities-sql-server.database.windows.net
SQL_DATABASE=urban_cities_db
SQL_USERNAME=sqladmin
SQL_PASSWORD=D030avbang@@
```

## 📊 Expected Workflow

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Extract    │  ← Fetch from NYC 311 API (incremental)
│   Data      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Transform   │  ← Clean, enrich, calculate quality
│   Data      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Load to    │  ← Upload raw + processed to ADLS
│   ADLS      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Trigger ADF │  ← NEW: Copy processed → SQL Database
│  Pipeline   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Update    │  ← Save last processed timestamp
│   State     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Cleanup    │  ← Remove temp files
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Notify    │  ← Send completion metrics
└──────┬──────┘
       │
       ▼
┌─────────────┐
│     END     │
└─────────────┘
```

## 🐛 Troubleshooting

### DAG Not Appearing
- Check DAG file syntax: `python dags/nyc_311_incremental_etl_azure.py`
- Restart scheduler: `docker restart airflow-scheduler`
- Check scheduler logs: `docker logs airflow-scheduler | grep ERROR`

### Import Errors
- Ensure ETL modules are in correct path
- Check Python path in DAG: `sys.path.insert(0, project_path)`
- Verify modules exist: `Extraction.py`, `Transformation.py`, `Loading_Azure.py`

### ADF Pipeline Fails
- Check Azure credentials are valid
- Verify pipeline name: `CopyProcessedDataToSQL`
- Check ADF pipeline exists in Azure Portal
- Review ADF pipeline run logs in Azure

### Authentication Errors
- Verify Service Principal credentials
- Check role assignments (Contributor + Storage Blob Data Owner)
- Test credentials: `python test_azure_connection.py`

### No Data Being Processed
- Check NYC 311 API is accessible
- Verify incremental extraction logic
- Review state file: `data/etl_state.json`
- Try manual extraction: `python Extraction.py`

## 📝 Monitoring Commands

```powershell
# View all containers
docker ps

# View DAG logs in real-time
docker logs -f airflow-scheduler

# Check Airflow database
docker exec -it airflow-webserver airflow db check

# List all DAGs
docker exec -it airflow-webserver airflow dags list

# Test DAG without running
docker exec -it airflow-webserver airflow dags test nyc_311_incremental_etl_azure 2025-11-04
```

## 🎯 Success Criteria

After successful execution, you should see:

1. ✅ All 9 tasks completed (green in Airflow UI)
2. ✅ New files in ADLS raw and processed containers
3. ✅ ADF pipeline run marked as "Succeeded" in Azure
4. ✅ New records in SQL Database with recent timestamps
5. ✅ Updated state file with latest processed timestamp
6. ✅ Notification task showing metrics summary

## 🔄 Schedule Configuration

Current schedule: **Every 15 minutes**
```python
schedule_interval=timedelta(minutes=15)
```

To change frequency, update this line in the DAG file and restart Airflow.

## 📧 Next Steps

1. **Test the DAG**: Run manual trigger and verify all steps
2. **Enable Scheduling**: Turn on DAG for automatic runs
3. **Set up Alerts**: Configure email/Slack notifications
4. **Monitor Performance**: Track execution times and data volumes
5. **Production Hardening**:
   - Add retry logic for API calls
   - Implement data validation checks
   - Set up monitoring dashboards
   - Configure backup strategies
