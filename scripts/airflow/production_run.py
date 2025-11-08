"""
Production Run Script - NYC 311 ETL Pipeline
Triggers the DAG and monitors execution
"""
import requests
import time
import json
from datetime import datetime

# Airflow configuration
AIRFLOW_URL = "http://localhost:8080"
DAG_ID = "nyc_311_incremental_etl_azure"
USERNAME = "admin"
PASSWORD = "admin"

def trigger_dag():
    """Trigger the NYC 311 ETL DAG"""
    print("=" * 60)
    print("NYC 311 ETL Pipeline - Production Run")
    print("=" * 60)
    print(f"\nTriggering DAG: {DAG_ID}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    url = f"{AIRFLOW_URL}/api/v1/dags/{DAG_ID}/dagRuns"
    
    payload = {
        "conf": {},
        "dag_run_id": f"manual_prod_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            auth=(USERNAME, PASSWORD),
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            dag_run_id = result.get('dag_run_id')
            print(f"✅ DAG triggered successfully!")
            print(f"   Run ID: {dag_run_id}")
            print(f"\n📊 Monitor progress at: {AIRFLOW_URL}/dags/{DAG_ID}/grid")
            return dag_run_id
        else:
            print(f"❌ Failed to trigger DAG: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error triggering DAG: {str(e)}")
        return None

def get_dag_run_status(dag_run_id):
    """Get the status of a DAG run"""
    url = f"{AIRFLOW_URL}/api/v1/dags/{DAG_ID}/dagRuns/{dag_run_id}"
    
    try:
        response = requests.get(
            url,
            auth=(USERNAME, PASSWORD)
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except Exception as e:
        print(f"Error checking status: {str(e)}")
        return None

def monitor_dag_run(dag_run_id, check_interval=10, max_wait=600):
    """Monitor DAG run until completion"""
    if not dag_run_id:
        return
    
    print(f"\n🔍 Monitoring DAG run: {dag_run_id}")
    print(f"   Checking every {check_interval} seconds (max {max_wait}s)\n")
    
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            print(f"\n⏱️  Monitoring timeout reached ({max_wait}s)")
            break
        
        status_data = get_dag_run_status(dag_run_id)
        
        if status_data:
            state = status_data.get('state')
            start_date = status_data.get('start_date', '')
            end_date = status_data.get('end_date', '')
            
            print(f"[{int(elapsed)}s] State: {state}", end='')
            
            if state == 'running':
                print(" ⏳")
            elif state == 'success':
                print(" ✅")
                print(f"\n🎉 DAG completed successfully!")
                print(f"   Duration: {int(elapsed)} seconds")
                if end_date:
                    print(f"   Completed at: {end_date}")
                break
            elif state == 'failed':
                print(" ❌")
                print(f"\n❌ DAG failed!")
                print(f"   Check logs at: {AIRFLOW_URL}/dags/{DAG_ID}/grid")
                break
            else:
                print(f" ({state})")
        
        time.sleep(check_interval)
    
    print("\n" + "=" * 60)

def print_next_steps():
    """Print next steps for verification"""
    print("\n📋 NEXT STEPS - Verify Production Run:")
    print("\n1. Check Azure Data Lake Storage:")
    print("   - Container: processed")
    print("   - Look for: nyc_311_processed_YYYYMMDD_HHMMSS.parquet")
    print("   - Verify: File has all 20 columns")
    
    print("\n2. Check Azure Data Factory:")
    print("   - Pipeline: CopyProcessedDataToSQL")
    print("   - Status: Should show 'Succeeded'")
    print("   - Rows copied: Should match parquet row count")
    
    print("\n3. Verify Azure SQL Database:")
    print("   Run this query:")
    print("""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(closed_date) as rows_with_closed_date,
        COUNT(resolution_hours) as rows_with_resolution_hours,
        AVG(CASE WHEN resolution_hours > 0 THEN resolution_hours END) as avg_resolution_hours,
        MAX(created_date) as latest_record,
        MAX(processed_at) as last_processed
    FROM nyc_311_requests;
    """)
    
    print("\n4. Check for data quality:")
    print("""
    SELECT TOP 5 
        unique_key, created_date, closed_date, agency, complaint_type,
        resolution_hours, is_closed, data_quality_score
    FROM nyc_311_requests 
    ORDER BY processed_at DESC;
    """)
    
    print("\n5. Schedule Information:")
    print("   - DAG runs automatically every 1 hour")
    print("   - Can be triggered manually anytime")
    print(f"   - UI: {AIRFLOW_URL}/dags/{DAG_ID}/grid")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    # Trigger the DAG
    dag_run_id = trigger_dag()
    
    # Monitor execution
    if dag_run_id:
        monitor_dag_run(dag_run_id, check_interval=15, max_wait=900)
    
    # Print next steps
    print_next_steps()
