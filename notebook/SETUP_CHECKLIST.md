# ✅ Airflow Setup Checklist

## Phase 1: Prerequisites (Complete these first)

### 🐳 Docker Installation
- [ ] Download Docker Desktop from https://www.docker.com/products/docker-desktop/
- [ ] Install Docker Desktop
- [ ] Restart your computer
- [ ] Start Docker Desktop application
- [ ] Verify: Open PowerShell and run `docker --version`
- [ ] Verify: Run `docker-compose --version`

### 🔧 System Requirements
- [x] Python 3.11+ installed
- [x] PowerShell available
- [x] Cryptography package installed
- [ ] At least 4GB RAM available
- [ ] At least 2GB disk space available

## Phase 2: Configuration

### 📝 Update Configuration Files
1. **Edit .env file** with your actual credentials:
   ```
   APP_TOKEN=your_actual_nyc_311_app_token
   AZURE_STORAGE_ACCOUNT_NAME=your_azure_storage_account
   ```

2. **Verify all files are in place:**
   - [x] Extraction.py
   - [x] Transformation.py  
   - [x] Loading.py
   - [x] dag_script.py
   - [x] dags/nyc_311_dag.py
   - [x] docker-compose.yml
   - [x] Dockerfile
   - [x] requirements.txt
   - [x] .env

## Phase 3: Docker Setup (Run after Docker is installed)

### 🚀 Automated Setup
```powershell
cd "c:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\notebook"
.\setup_airflow.ps1
```

### 🔄 Manual Setup (if automated fails)
```powershell
# 1. Build Docker images
docker-compose build

# 2. Initialize database
docker-compose run --rm airflow-webserver airflow db init

# 3. Create admin user
docker-compose run --rm airflow-webserver airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin

# 4. Start services
docker-compose up -d

# 5. Check status
docker-compose ps
```

## Phase 4: Verification

### 🌐 Access Airflow
- [ ] Open browser to http://localhost:8080
- [ ] Login with username: `admin`, password: `admin`
- [ ] Verify DAG `nyc_311_incremental_etl` appears
- [ ] Enable the DAG
- [ ] Trigger a test run

### 🔍 Verify Services
```powershell
# Check all services are running
docker-compose ps

# Check logs for errors
docker-compose logs airflow-webserver
docker-compose logs airflow-scheduler
```

## Phase 5: Testing

### 🧪 Test Your Pipeline
1. **Manual DAG Trigger:**
   - Go to Airflow UI
   - Find your DAG: `nyc_311_incremental_etl`
   - Click "Trigger DAG"
   - Monitor execution

2. **Command Line Testing:**
   ```powershell
   # Test DAG syntax
   docker-compose exec airflow-webserver python -m py_compile /opt/airflow/dags/nyc_311_dag.py
   
   # Trigger DAG
   docker-compose exec airflow-webserver airflow dags trigger nyc_311_incremental_etl
   ```

## 🆘 Troubleshooting Guide

### Common Issues & Solutions

1. **Docker not found**
   - Install Docker Desktop
   - Restart PowerShell after installation
   - Ensure Docker Desktop is running

2. **Port 8080 in use**
   ```powershell
   netstat -ano | findstr :8080
   # Kill the process or change port in docker-compose.yml
   ```

3. **Build failures**
   ```powershell
   # Clean and rebuild
   docker-compose down -v
   docker system prune -f
   docker-compose build --no-cache
   ```

4. **Database issues**
   ```powershell
   # Reset database
   docker-compose down -v
   docker-compose up -d
   ```

5. **DAG not appearing**
   - Check DAG file syntax
   - Restart scheduler: `docker-compose restart airflow-scheduler`
   - Check logs: `docker-compose logs airflow-scheduler`

## 📋 Quick Reference Commands

### Service Management
```powershell
docker-compose up -d          # Start services
docker-compose down           # Stop services  
docker-compose restart        # Restart services
docker-compose ps            # Check status
```

### Logs & Debugging
```powershell
docker-compose logs                    # All logs
docker-compose logs airflow-webserver  # Web server logs
docker-compose logs airflow-scheduler  # Scheduler logs
docker-compose logs -f                 # Follow logs real-time
```

### DAG Operations
```powershell
# List DAGs
docker-compose exec airflow-webserver airflow dags list

# Trigger DAG
docker-compose exec airflow-webserver airflow dags trigger nyc_311_incremental_etl

# Test specific task
docker-compose exec airflow-webserver airflow tasks test nyc_311_incremental_etl extract_transform_load 2025-10-31
```

## 🎯 Success Criteria

Your setup is successful when:
- [x] All Docker containers are running
- [x] Airflow Web UI is accessible at http://localhost:8080
- [x] Your DAG appears in the DAGs list
- [x] DAG can be triggered and runs successfully
- [x] Data processing completes without errors
- [x] Logs show successful ETL execution

## 📞 Next Steps After Setup

1. **Configure API Credentials** - Add your real NYC 311 API token
2. **Setup Azure Storage** - Configure Azure Data Lake credentials  
3. **Email Notifications** - Configure SMTP for failure alerts
4. **Production Security** - Change default passwords and keys
5. **Monitoring** - Set up log aggregation and alerting
6. **Backup Strategy** - Implement regular data and config backups

---

**Ready to proceed?** Start with Phase 1 (Docker installation) if you haven't already! 🚀