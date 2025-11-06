# Setup Completion Summary

## Date: November 4, 2025

## ✅ Completed Tasks

### 1. Azure Data Factory Pipeline Setup
**Status:** ✅ COMPLETED

Created ADF resources:
- **Linked Services:**
  - `AzureDataLakeStorage_LinkedService` - Connects to urbancitiesadls2025
  - `AzureSqlDatabase_LinkedService` - Connects to urban_cities_db

- **Datasets:**
  - `SourceDataset_ADLS_CSV` - Points to processed container (processed-data/)
  - `SinkDataset_SQL_Table` - Points to nyc_311_requests table

- **Pipeline:**
  - `CopyProcessedDataToSQL` - Copies data from ADLS to SQL Database

**Authentication:** Service Principal (infrastructure-independent)

### 2. Azure SQL Database Table
**Status:** ✅ COMPLETED

- **Table:** `dbo.nyc_311_requests`
- **Columns:** 27 (including derived columns from transformation)
- **Primary Key:** `unique_key`
- **Indexes:** 6 indexes for optimized queries
  - idx_created_date
  - idx_agency
  - idx_complaint_type
  - idx_borough
  - idx_status
  - idx_created_year_month

### 3. SQL Server Firewall Rule
**Status:** ✅ COMPLETED

- **Rule Name:** AllowCurrentIP
- **IP Address:** 109.154.172.101
- **Access:** Enabled for local development

### 4. ETL Pipeline Testing
**Status:** ✅ COMPLETED

Test script (`test_etl_pipeline.py`) successfully:
- ✅ Initialized all ETL components
- ✅ Extracted data from NYC 311 API (or sample data)
- ✅ Transformed data with quality metrics
- ✅ Loaded to ADLS raw container
- ✅ Loaded to ADLS processed container

---

## 📋 Next Steps

### Immediate: Test End-to-End Workflow

1. **Run Fresh ETL Test:**
   ```powershell
   python test_etl_pipeline.py
   ```
   This will create new files in ADLS containers.

2. **Trigger ADF Pipeline:**
   - Option A: Azure Portal
     - Navigate to Data Factory → CopyProcessedDataToSQL
     - Click "Debug" or "Trigger Now"
   
   - Option B: Python Script (we can create this)
     - Programmatically trigger pipeline
     - Monitor execution

3. **Verify Data in SQL:**
   ```sql
   SELECT COUNT(*) FROM nyc_311_requests;
   SELECT TOP 10 * FROM nyc_311_requests ORDER BY created_date DESC;
   ```

### Future: Airflow Integration

1. **Review Airflow DAG:**
   - File: `dags/nyc_311_incremental_etl_azure.py`
   - 7 tasks: extract → transform → load_to_azure → trigger_adf → update_state → cleanup → notify

2. **Start Airflow:**
   ```powershell
   docker-compose up -d
   ```

3. **Access Airflow UI:**
   - URL: http://localhost:8080
   - Username: admin
   - Password: admin

4. **Enable and Test DAG:**
   - Enable `nyc_311_incremental_etl_azure` DAG
   - Trigger manual run
   - Monitor all 7 tasks

---

## 🔧 Scripts Created

| Script | Purpose | Status |
|--------|---------|--------|
| `test_etl_pipeline.py` | Test complete ETL workflow | ✅ Working |
| `create_adf_pipeline.py` | Setup ADF resources | ✅ Complete |
| `create_sql_table.py` | Create SQL table schema | ✅ Complete |
| `add_sql_firewall_rule.py` | Enable SQL access | ✅ Complete |
| `verify_azure_files.py` | List files in ADLS | ✅ Available |
| `test_azure_connection.py` | Test Azure auth | ✅ Working |

---

## 🔐 Authentication Summary

**Service Principal:**
- Client ID: `27b470a2-fa5d-458a-85d5-e639c0791f23`
- Tenant ID: `edc41ca9-a02a-4623-97cb-2a58f19e3c46`
- Roles: Contributor + Storage Blob Data Owner
- Status: ✅ Infrastructure-independent authentication active

**Azure Resources:**
- Storage Account: `urbancitiesadls2025`
- SQL Server: `urban-cities-sql-server.database.windows.net`
- Database: `urban_cities_db`
- Data Factory: `urban-cities-adf`
- Resource Group: `urban-cities-rg`

---

## 📊 Data Flow Architecture

```
NYC 311 API
    ↓
[Extract] → DataFrame (Extraction.py)
    ↓
[Transform] → Quality Metrics + Derived Columns (Transformation.py)
    ↓
[Load Raw] → ADLS raw/raw-data/*.csv (Loading_Azure.py)
    ↓
[Load Processed] → ADLS processed/processed-data/*.csv (Loading_Azure.py)
    ↓
[ADF Pipeline] → Copy processed data (CopyProcessedDataToSQL)
    ↓
[Azure SQL] → nyc_311_requests table
    ↓
[Analytics/Reports] → Power BI / SQL Queries
```

---

## 🎯 Success Metrics

- ✅ Service Principal authentication working
- ✅ ETL pipeline extracts, transforms, and loads data
- ✅ Data successfully uploaded to ADLS (both raw and processed)
- ✅ ADF pipeline created and configured
- ✅ SQL table created with proper schema
- ✅ Firewall access enabled for local development

**Ready for:** End-to-end testing with ADF → SQL integration

---

## 🚀 Quick Commands Reference

### Test ETL Pipeline:
```powershell
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\notebook"
python test_etl_pipeline.py
```

### Start Airflow:
```powershell
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\notebook"
docker-compose up -d
```

### Query SQL Database (in Python):
```python
import pyodbc
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=urban-cities-sql-server.database.windows.net;"
    "DATABASE=urban_cities_db;"
    "UID=sqladmin;"
    "PWD=D030avbang@@"
)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM nyc_311_requests")
print(f"Total records: {cursor.fetchone()[0]}")
```

---

## 📝 Notes

- Test files were deleted from ADLS containers - ready for fresh test
- SQL Server firewall rule is IP-specific (may need update if IP changes)
- ADF pipeline uses Service Principal authentication (no keys needed)
- All sensitive credentials are in `.env` file (not committed to Git)

