# 🚀 Apache Airflow + Docker Setup Guide

## Overview
This guide will help you set up Apache Airflow with Docker for your NYC 311 ETL pipeline. Your pipeline will run as scheduled DAGs with proper monitoring and error handling.

## Prerequisites
- Docker Desktop installed and running
- Python 3.11+ with pip
- Git (optional)

## Quick Setup (Recommended)

### Option 1: Automated Setup (Windows PowerShell)
```powershell
# Navigate to your project directory
cd "c:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\notebook"

# Run the automated setup script
.\setup_airflow.ps1
```

### Option 2: Manual Step-by-Step Setup

#### Step 1: Configure Environment Variables
Edit the `.env` file with your actual credentials:
```bash
# Update these with your actual values
APP_TOKEN=your_actual_app_token_here
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account
AIRFLOW__CORE__FERNET_KEY=YGF1v3nLswkxzfCHRHFhT3pRWNGGAc1X7RM4G36qh6A=
```

#### Step 2: Build and Start Services
```powershell
# Build Docker images
docker-compose build

# Initialize Airflow database
docker-compose run --rm airflow-webserver airflow db init

# Create admin user
docker-compose run --rm airflow-webserver airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin

# Start all services
docker-compose up -d
```

#### Step 3: Verify Setup
```powershell
# Check service status
docker-compose ps

# View logs
docker-compose logs airflow-webserver
docker-compose logs airflow-scheduler
```

## Accessing Airflow

### Web Interface
- **URL**: http://localhost:8080
- **Username**: admin
- **Password**: admin

### Your DAG
Your NYC 311 ETL pipeline will appear as: `nyc_311_incremental_etl`

## Project Structure
```
notebook/
├── Extraction.py              # Data extraction module
├── Transformation.py          # Data transformation module  
├── Loading.py                 # Data loading module
├── dag_script.py             # Original DAG definition
├── dags/
│   ├── nyc_311_dag.py        # Your DAG for Airflow
│   └── nyc_311_incremental_etl.py
├── data/                     # Data directory (mounted in Docker)
├── logs/                     # Airflow logs
├── plugins/                  # Airflow plugins
├── docker-compose.yml        # Docker services configuration
├── Dockerfile               # Airflow container definition
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── setup_airflow.ps1        # Automated setup script
```

## Key Features

### 🔄 Scheduled Execution
- Runs every 15 minutes
- Incremental data processing
- Automatic state management

### 📊 Monitoring
- Web UI dashboard
- Task success/failure tracking
- Detailed logs for debugging

### 🛡️ Error Handling
- Automatic retries (3 attempts)
- Email notifications on failure
- Data quality validation

### 💾 Data Persistence
- PostgreSQL database for Airflow metadata
- Local data directory for ETL state
- Azure Data Lake for processed data

## Common Commands

### Service Management
```powershell
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View service status
docker-compose ps
```

### Monitoring & Debugging
```powershell
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs airflow-webserver
docker-compose logs airflow-scheduler
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f airflow-scheduler
```

### DAG Management
```powershell
# List all DAGs
docker-compose exec airflow-webserver airflow dags list

# Test a specific task
docker-compose exec airflow-webserver airflow tasks test nyc_311_incremental_etl extract_transform_load 2025-10-31

# Trigger DAG manually
docker-compose exec airflow-webserver airflow dags trigger nyc_311_incremental_etl
```

### Database Management
```powershell
# Access Airflow database
docker-compose exec postgres psql -U airflow -d airflow

# Reset database (if needed)
docker-compose down -v
docker-compose up -d
```

## Configuration

### Environment Variables (.env file)
```bash
# NYC 311 API
NYC_311_API_URL=https://data.cityofnewyork.us/resource/erm2-nwe9.json
APP_TOKEN=your_app_token_here
BATCH_SIZE=1000

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account_name
AZURE_CONTAINER_NAME=nyc-311-data
AZURE_DIRECTORY_NAME=incremental

# Airflow Security
AIRFLOW__CORE__FERNET_KEY=YGF1v3nLswkxzfCHRHFhT3pRWNGGAc1X7RM4G36qh6A=
AIRFLOW__WEBSERVER__SECRET_KEY=your_secret_key_here
```

### DAG Configuration
Your DAG is configured with:
- **Schedule**: Every 15 minutes
- **Retries**: 3 attempts with 5-minute delays
- **Timeout**: 30 minutes per task
- **Email notifications**: On failure
- **Concurrency**: 1 DAG run at a time

## Troubleshooting

### Common Issues

#### 1. Port 8080 Already in Use
```powershell
# Find what's using the port
netstat -ano | findstr :8080

# Kill the process or change port in docker-compose.yml
```

#### 2. Database Connection Issues
```powershell
# Restart postgres service
docker-compose restart postgres

# Check postgres logs
docker-compose logs postgres
```

#### 3. DAG Not Appearing
```powershell
# Check if DAG file is valid
docker-compose exec airflow-webserver python -m py_compile /opt/airflow/dags/nyc_311_dag.py

# Refresh DAGs
docker-compose exec airflow-webserver airflow dags reserialize
```

#### 4. Permission Issues
```powershell
# Fix directory permissions
docker-compose exec airflow-webserver chown -R airflow:airflow /opt/airflow/logs
```

### Logs Location
- **Container logs**: `docker-compose logs [service_name]`
- **Airflow logs**: `./logs/` directory
- **Task logs**: Available in Web UI under each task

## Production Considerations

### Security
- Change default passwords
- Use secure Fernet keys
- Configure proper authentication
- Set up HTTPS/TLS

### Scaling
- Use CeleryExecutor for multiple workers
- Add Redis for task queuing
- Configure proper resource limits

### Monitoring
- Set up proper alerting
- Configure log aggregation
- Monitor resource usage

### Backup
- Regular database backups
- State file backups
- Configuration backups

## Next Steps

1. **Configure your API tokens** in the `.env` file
2. **Run the setup script**: `.\setup_airflow.ps1`
3. **Access the Web UI**: http://localhost:8080
4. **Enable your DAG** and monitor execution
5. **Set up Azure credentials** for cloud storage
6. **Configure email notifications** for production alerts

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs`
2. Verify your configuration in `.env`
3. Ensure Docker Desktop is running
4. Check port availability (8080, 5432)
5. Validate your DAG syntax

Your NYC 311 ETL pipeline is now ready for production with full orchestration, monitoring, and error handling! 🎉