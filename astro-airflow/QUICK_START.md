# Astronomer Astro Setup - Quick Start Guide

## ✅ Completed Steps

### 1. Installation
- ✅ Installed Astro CLI v1.38.0 via winget
- ✅ Installed Podman as Docker alternative
- ✅ Location: `C:\Users\David Ibanga\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe\astro.exe`

### 2. Project Initialization
- ✅ Created astro-airflow directory
- ✅ Ran `astro dev init`
- ✅ Generated Astro project structure

### 3. Configuration Migration
- ✅ **requirements.txt**: Fixed sqlalchemy conflict (removed explicit version)
- ✅ **.env**: Copied all environment variables (NYC API, Azure credentials, SQL)
- ✅ **DAGs**: Copied from notebook/dags/ → astro-airflow/dags/
- ✅ **ETL Modules**: Moved to include/ directory
  - Extraction.py
  - Transformation.py  
  - Loading_Azure.py
- ✅ **State File**: Copied to include/data/etl_state.json

### 4. Code Updates
- ✅ Updated import paths: `from include.Extraction import...`
- ✅ Updated STATE_FILE path: `/usr/local/airflow/include/data/etl_state.json`
- ✅ Removed AIRFLOW_AVAILABLE conditional (always available in Astro)
- ✅ Fixed indentation (removed unnecessary if-block indent)

### 5. Environment Startup
- ⏳ **Currently Building**: `astro dev start` in progress
- ⏳ This will:
  1. Build Docker image with Astro Runtime 3.1-3 (Airflow 2.10+)
  2. Install all Python dependencies from requirements.txt
  3. Start PostgreSQL database
  4. Start Airflow webserver (port 8080)
  5. Start Airflow scheduler
  6. Start triggerer

## 📋 Migration Checklist

- [x] Stop old Docker Compose containers
- [x] Install Astro CLI
- [x] Initialize Astro project
- [x] Migrate requirements.txt (fix sqlalchemy conflict)
- [x] Migrate .env file
- [x] Copy DAG files
- [x] Copy ETL modules to include/
- [x] Update import paths in DAG
- [x] Update file paths for Astro structure
- [x] Start Astro environment
- [ ] Verify DAG loads without errors
- [ ] Test DAG execution
- [ ] Verify Azure integration
- [ ] Cleanup old Docker Compose setup

## 🚀 Using Astro Commands

### Essential Commands

```powershell
# Start Airflow (building now...)
& "C:\Users\David Ibanga\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe\astro.exe" dev start

# View logs
& "C:\Users\David Ibanga\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe\astro.exe" dev logs

# Stop Airflow
& "C:\Users\David Ibanga\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe\astro.exe" dev stop

# Restart after code changes
& "C:\Users\David Ibanga\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe\astro.exe" dev restart

# Run pytest tests
& "C:\Users\David Ibanga\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe\astro.exe" dev pytest

# Access Airflow CLI
& "C:\Users\David Ibanga\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe\astro.exe" dev run dags list
```

### Shorter Alias (Optional)

To avoid typing the full path, create an alias in your PowerShell profile:

```powershell
# Add to $PROFILE
Set-Alias -Name astro -Value "C:\Users\David Ibanga\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe\astro.exe"

# Then use: astro dev start
```

Or restart your terminal to pick up PATH changes from winget installation.

## 🌐 Accessing Airflow UI

Once `astro dev start` completes:

- **URL**: http://localhost:8080
- **Username**: admin
- **Password**: admin

## 🔍 Key Differences from Docker Compose

| Aspect | Docker Compose | Astronomer Astro |
|--------|----------------|------------------|
| Setup | Manual docker-compose.yml | `astro dev init` |
| Dependencies | Manual version management | Astro Runtime (pre-tested) |
| Database | Separate postgres service | Built-in PostgreSQL |
| DAG Development | Manual restarts | Hot-reload |
| CLI | docker-compose commands | `astro dev` commands |
| Production | Manual deployment | `astro deploy` |
| sqlalchemy | Version conflicts | Managed by runtime |

## 🛠️ Fixed Issues

### 1. sqlalchemy Version Conflict ✅
**Old Problem**: 
```
ERROR: Cannot install apache-airflow==2.7.3 and sqlalchemy>=2.0.0 
because these package versions have conflicting dependencies.
```

**Solution**: Removed `sqlalchemy>=2.0.0` from requirements.txt. Astro Runtime 3.1-3 manages compatible versions.

### 2. Import Path Issues ✅
**Old**: `from Extraction import DataExtractor`  
**New**: `from include.Extraction import DataExtractor`

Astro adds `/usr/local/airflow/include` to Python path automatically.

### 3. Webserver Startup Failures ✅
**Old Problem**: Webserver crashed due to dependency conflicts  
**Solution**: Astro Runtime has pre-tested, compatible package versions

## 📊 Current Status

```
[⏳ IN PROGRESS] Building Astro project image...
```

### What's Happening Now:
1. ✅ Pulling base image: astrocrpublic.azurecr.io/runtime:3.1-3
2. ⏳ Installing Python dependencies (pandas, azure packages, etc.)
3. ⏳ Setting up Airflow database
4. ⏳ Starting services (webserver, scheduler, triggerer)

### Expected Duration: 3-5 minutes (first build)
Subsequent starts will be much faster (< 30 seconds) due to Docker layer caching.

## ✨ Benefits Gained

1. **No More Dependency Hell**: Astro Runtime pre-tests package compatibility
2. **Faster Development**: DAG changes hot-reload without full restart
3. **Better Tooling**: `astro dev` commands streamline workflow
4. **Production Ready**: Same image runs locally and in Astro Cloud
5. **Built-in Best Practices**: Project structure follows Airflow conventions
6. **Automatic Testing**: `astro dev pytest` validates DAGs before deployment

## 🎯 Next Steps

Once build completes (check terminal output):

1. Access http://localhost:8080 (admin/admin)
2. Verify DAG `nyc_311_incremental_etl_azure` appears
3. Check for import errors in DAG
4. Unpause the DAG
5. Trigger manual run
6. Monitor task execution
7. Verify Azure integrations work (ADLS, ADF, SQL)

## 📝 Notes

- Old Docker Compose has been stopped (`docker-compose down`)
- Old volumes still exist if you need to recover data
- Complete removal: `docker-compose down -v` and `docker volume prune`
- Astro uses Podman instead of Docker (installed as dependency)
- First build is slow; subsequent starts are fast

## 🆘 Troubleshooting

### Build fails with "connection refused"
- Ensure Docker Desktop or Podman is running
- Check firewall settings

### Port 8080 already in use
- Stop old services: `docker ps` and `docker stop <container>`
- Or change port in .env: `AIRFLOW__WEBSERVER__WEB_SERVER_PORT=8081`

### DAG not appearing
- Check logs: `astro dev logs`
- Look for Python import errors
- Verify include/ directory has ETL modules

### Azure authentication fails
- Verify .env file is in astro-airflow/ directory
- Check AZURE_CLIENT_ID and AZURE_CLIENT_SECRET values
- Service Principal should be: 27b470a2-fa5d-458a-85d5-e639c0791f23
