# 🚀 Quick Start Commands (After Build Completes)

## Setup Commands (Run in order)

### 1. Initialize Airflow Database
```powershell
cd "c:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\notebook"
$env:PATH += ";C:\Program Files\Docker\Docker\resources\bin"
docker-compose run --rm airflow-webserver airflow db init
```

### 2. Create Admin User
```powershell
docker-compose run --rm airflow-webserver airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin
```

### 3. Start All Services
```powershell
docker-compose up -d
```

### 4. Check Status
```powershell
docker-compose ps
```

## Access Airflow
- **URL**: http://localhost:8080
- **Username**: admin
- **Password**: admin

## Your DAG
Look for: `nyc_311_incremental_etl`

## Useful Commands

### Service Management
```powershell
docker-compose up -d      # Start services
docker-compose down       # Stop services
docker-compose restart    # Restart services
docker-compose logs       # View logs
```

### DAG Management
```powershell
# List DAGs
docker-compose exec airflow-webserver airflow dags list

# Trigger your DAG
docker-compose exec airflow-webserver airflow dags trigger nyc_311_incremental_etl

# Check DAG status
docker-compose exec airflow-webserver airflow dags state nyc_311_incremental_etl
```

### Troubleshooting
```powershell
# View specific service logs
docker-compose logs airflow-webserver
docker-compose logs airflow-scheduler
docker-compose logs postgres

# Restart if needed
docker-compose restart airflow-scheduler
docker-compose restart airflow-webserver
```

## Quick Test Your Pipeline
1. Open http://localhost:8080
2. Find "nyc_311_incremental_etl" DAG
3. Turn it ON (toggle switch)
4. Click "Trigger DAG" to test manually
5. Monitor execution in the UI

Ready to proceed when Docker build completes! 🎯