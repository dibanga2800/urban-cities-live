# Architecture Overview

## System Architecture

```
┌─────────────────┐
│  NYC 311 API    │
│  (Public Data)  │
└────────┬────────┘
         │ HTTP GET (SoQL)
         ↓
┌─────────────────────────────────┐
│   Apache Airflow (Astro)        │
│  ┌──────────┐  ┌──────────┐    │
│  │ Extract  │→ │Transform │    │
│  └──────────┘  └────┬─────┘    │
└─────────────────────┼───────────┘
                      │
         ┌────────────┴────────────┐
         ↓                         ↓
┌──────────────────┐      ┌───────────────┐
│ Raw CSV Upload   │      │ Processed     │
│ (nyc_311_raw.csv)│      │ Parquet Upload│
└────────┬─────────┘      └───────┬───────┘
         │                        │
         ↓                        ↓
┌─────────────────────────────────────┐
│   Azure Data Lake Storage Gen2      │
│   ┌─────────┐      ┌──────────┐   │
│   │  raw/   │      │processed/│   │
│   └─────────┘      └────┬─────┘   │
└──────────────────────────┼──────────┘
                           │
                           ↓
              ┌────────────────────────┐
              │ Azure Data Factory     │
              │ (Copy Pipeline)        │
              └────────┬───────────────┘
                       │
                       ↓
              ┌────────────────────────┐
              │ Azure SQL Database     │
              │ (nyc_311_requests)     │
              └────────────────────────┘
```

## Component Details

### 1. Data Source
- **NYC 311 API**: Public API providing service request data
- **Endpoint**: `https://data.cityofnewyork.us/resource/erm2-nwe9.json`
- **Protocol**: HTTP GET with SoQL queries
- **Rate Limit**: Unauthenticated requests limited to 1,000/day

### 2. Apache Airflow Orchestration
- **Runtime**: Astronomer Astro 3.1-3 (based on Airflow 2.10)
- **Deployment**: Local Docker containers
- **Schedule**: Hourly (`0 * * * *`)
- **Components**:
  - Scheduler: Manages DAG execution
  - Webserver: UI on port 8080
  - DAG Processor: Parses DAG files
  - Triggerer: Handles deferred tasks

### 3. ETL Pipeline

#### Extract Phase
- Queries NYC 311 API for new records since last successful run
- Uses SoQL `$where` clause for incremental loading
- Batch size: 5,000 records per request
- State tracking: `etl_state.json` stores last processed timestamp

#### Transform Phase
- Data cleaning and standardization
- Feature engineering:
  - `unique_key`: Hash-based deduplication key
  - `resolution_time_hours`: Time to close request
  - `data_quality_score`: Completeness metric (0-100)
  - `is_closed_same_day`: Boolean flag
- Schema validation: Ensures 20 expected columns

#### Load Phase
- **Single-File Approach**: Appends to master files
- **Raw**: `nyc_311_raw.csv` in ADLS raw container
- **Processed**: `nyc_311_processed.parquet` in ADLS processed container
- **Deduplication**: Removes duplicates based on `unique_key` (keeps latest)

### 4. Azure Data Lake Storage Gen2
- **Storage Account**: `urbancitiesadls2025`
- **Containers**:
  - `raw/`: Raw CSV data
  - `processed/`: Cleaned Parquet data
  - `curated/`: Reserved for aggregations (future)
- **Authentication**: Service Principal with Storage Blob Data Contributor role
- **Format**: Hierarchical namespace enabled

### 5. Azure Data Factory
- **Pipeline**: `CopyProcessedDataToSQL`
- **Source**: ADLS processed container (Parquet format)
- **Sink**: Azure SQL Database
- **Copy Mode**: TRUNCATE then INSERT (full reload)
- **Trigger**: Programmatic from Airflow after successful load
- **Linked Services**:
  - ADLS Gen2 (service principal auth)
  - Azure SQL Database (SQL auth)

### 6. Azure SQL Database
- **Server**: `urban-cities-sql-srv-2025.database.windows.net`
- **Database**: `urban_cities_db`
- **Table**: `nyc_311_requests`
- **Schema**: 20 columns matching transformed data
- **Primary Key**: `unique_key` (NVARCHAR(100))
- **Indexes**: Clustered index on `unique_key`

## Data Flow Details

### Incremental Processing
1. Airflow reads last successful timestamp from `etl_state.json`
2. API query: `$where=created_date > '{last_timestamp}'`
3. Transform new records only
4. Append to existing ADLS files with deduplication
5. Update `etl_state.json` with latest timestamp

### Deduplication Strategy
- **Location**: Python code before upload to ADLS
- **Key**: `unique_key` column (hash of request attributes)
- **Method**: Pandas `drop_duplicates(subset=['unique_key'], keep='last')`
- **Rationale**: Keeps most recent version of each request

### Error Handling
- Failed DAG tasks are retried automatically (Airflow default: 0 retries)
- State file only updates after successful load
- Failed runs can be reprocessed without data loss
- Azure services have built-in retry mechanisms

## Network Architecture

```
┌──────────────────────────────────────────┐
│         Local Development                │
│  ┌────────────────────────────────────┐  │
│  │   Docker (Astro Containers)        │  │
│  │   - Port 8080: Airflow UI          │  │
│  │   - Port 5432: PostgreSQL          │  │
│  └────────────────┬───────────────────┘  │
└───────────────────┼──────────────────────┘
                    │
                    │ HTTPS (TLS 1.2+)
                    ↓
┌──────────────────────────────────────────┐
│         Azure Cloud (East US)            │
│  ┌────────────────────────────────────┐  │
│  │  urbancitiesadls2025               │  │
│  │  (Data Lake Gen2)                  │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  urban-cities-adf                  │  │
│  │  (Data Factory)                    │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  urban-cities-sql-srv-2025         │  │
│  │  (SQL Database)                    │  │
│  │  - Firewall: Client IP allowed     │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

## Security Model

### Authentication Methods
- **Airflow → ADLS**: Service Principal (OAuth 2.0)
- **Airflow → ADF**: Service Principal + Azure Management SDK
- **ADF → ADLS**: Managed Identity or Service Principal
- **ADF → SQL**: SQL Authentication
- **Developer → Azure**: Azure CLI (interactive login)

### Authorization (RBAC)
- Service Principal roles:
  - `Storage Blob Data Contributor` on ADLS
  - `Data Factory Contributor` on ADF
- SQL Database:
  - `sqladmin` user with db_owner role

### Network Security
- SQL Database: Firewall rules restrict access by IP
- ADLS: Public access disabled, authentication required
- ADF: Integrated with Azure Active Directory

## Scalability Considerations

### Current Scale
- **Data Volume**: ~500 MB Parquet file (all historical data)
- **API Frequency**: Hourly extractions
- **Processing Time**: ~3-5 minutes per DAG run
- **SQL Database**: Basic tier (sufficient for current load)

### Scale-Out Options
- **Increase Frequency**: Change schedule to every 30 minutes or 15 minutes
- **Larger Batches**: Increase API batch size from 5,000 to 10,000 records
- **Parallel Processing**: Add concurrent DAG runs (with careful state management)
- **SQL Scaling**: Upgrade to Standard or Premium tier for more DTUs
- **Airflow Scaling**: Deploy to Kubernetes for horizontal scaling

## Technology Choices

### Why Airflow?
- Industry standard for workflow orchestration
- Python-native (matches data processing language)
- Rich UI for monitoring and debugging
- Extensive integration ecosystem

### Why Azure Data Lake Gen2?
- Hierarchical namespace for efficient file operations
- High throughput for large data files
- Native integration with Azure Data Factory
- Cost-effective storage for analytics

### Why Parquet?
- Columnar format optimized for analytics
- Built-in compression (Snappy)
- Schema evolution support
- Fast read performance for SQL queries

### Why Single-File Approach?
- Simplified file management (2 files vs 50+)
- Eliminates file tracking complexity
- Easier to query full history
- Deduplication handled in Python (more flexible)
- ADF pipeline configuration simplified
