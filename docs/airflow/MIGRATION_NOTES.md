# Airflow Migration to Astronomer Astro

## Migration Summary

Successfully migrated from Docker Compose Airflow to Astronomer Astro CLI.

### What Was Migrated

1. **DAGs**: All DAG files from `notebook/dags/` → `astro-airflow/dags/`
2. **ETL Modules**: Extraction.py, Transformation.py, Loading_Azure.py → `astro-airflow/include/`
3. **Dependencies**: Updated requirements.txt (removed sqlalchemy version conflict)
4. **Environment Variables**: Complete .env file with Azure credentials
5. **State Files**: etl_state.json → `astro-airflow/include/data/`

### Key Changes

#### Import Paths
- **Old**: `from Extraction import DataExtractor`
- **New**: `from include.Extraction import DataExtractor`

#### State File Path
- **Old**: `os.path.join(project_path, 'data', 'etl_state.json')`
- **New**: `/usr/local/airflow/include/data/etl_state.json`

#### Dependency Fix
- **Issue**: sqlalchemy>=2.0.0 conflicted with apache-airflow 2.7.3
- **Solution**: Removed explicit sqlalchemy version (Astro Runtime manages it)

### Astro Project Structure

```
astro-airflow/
├── .astro/                    # Astro CLI configuration
├── dags/                      # DAG files
│   ├── nyc_311_incremental_etl_azure.py
│   ├── Transformation.py
│   └── __pycache__/
├── include/                   # Shared code (replaces notebook root)
│   ├── Extraction.py
│   ├── Transformation.py
│   ├── Loading_Azure.py
│   └── data/
│       └── etl_state.json
├── plugins/                   # Airflow plugins
├── tests/                     # DAG tests
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Astro Runtime base image
├── packages.txt               # OS-level packages
└── airflow_settings.yaml      # Airflow connections/variables
```

### Configuration Preserved

✅ Airflow executor: LocalExecutor  
✅ Database: PostgreSQL (managed by Astro)  
✅ Fernet key: YGF1v3nLswkxzfCHRHFhT3pRWNGGAc1X7RM4G36qh6A=  
✅ DAG pause on creation: true  
✅ Load examples: false  
✅ NYC 311 API token: 6M3sBUhJT4PT8ffBXXHjpjrTd  
✅ Azure Service Principal: 27b470a2-fa5d-458a-85d5-e639c0791f23  
✅ All Azure resource names and credentials

### How to Use

1. **Start Astro environment**:
   ```powershell
   cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\astro-airflow"
   astro dev start
   ```

2. **Access Airflow UI**:
   - URL: http://localhost:8080
   - Username: admin
   - Password: admin

3. **View logs**:
   ```powershell
   astro dev logs
   ```

4. **Stop environment**:
   ```powershell
   astro dev stop
   ```

5. **Restart after changes**:
   ```powershell
   astro dev restart
   ```

### Benefits of Astro

1. **No Dependency Conflicts**: Astro Runtime manages compatible package versions
2. **Faster Development**: Hot-reload for DAG changes
3. **Better CLI**: `astro dev` commands simplify management
4. **Production Ready**: Easy deployment to Astro Cloud
5. **Built-in Testing**: `astro dev pytest` for DAG validation
6. **Automatic Postgres**: No separate database setup needed

### Testing Checklist

- [ ] Start Astro environment: `astro dev start`
- [ ] Access UI at http://localhost:8080
- [ ] Verify DAG appears: `nyc_311_incremental_etl_azure`
- [ ] Check DAG imports without errors
- [ ] Trigger DAG manually
- [ ] Verify all 9 tasks execute
- [ ] Check Azure integration (ADLS, ADF, SQL)
- [ ] Confirm state file updates
- [ ] Review logs for any warnings

### Troubleshooting

**Issue**: DAG import errors  
**Solution**: Check `astro dev logs` for Python import errors, verify include/ path

**Issue**: Azure authentication fails  
**Solution**: Verify .env file has correct AZURE_CLIENT_ID and AZURE_CLIENT_SECRET

**Issue**: State file not found  
**Solution**: Ensure `/usr/local/airflow/include/data/` directory exists in container

**Issue**: Port 8080 already in use  
**Solution**: Stop old Docker Compose: `docker-compose -f docker-compose-airflow.yml down`

### Old Docker Compose Cleanup

The old Docker Compose setup has been stopped. To completely remove it:

```powershell
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\notebook"
docker-compose -f docker-compose-airflow.yml down -v  # Remove volumes too
docker volume prune  # Clean up unused volumes
```

### Next Steps

1. ✅ Start Astro environment
2. ⏳ Verify DAG execution
3. ⏳ Set up Airflow connections (if needed)
4. ⏳ Configure email notifications
5. ⏳ Deploy to Astro Cloud (optional)
