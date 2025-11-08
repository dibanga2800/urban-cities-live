"""
Check DAG Run Status - Quick monitoring
"""
import subprocess
import time
from datetime import datetime

def check_latest_run():
    """Check the latest DAG run status from logs"""
    print("=" * 70)
    print(f"NYC 311 ETL Pipeline Status Check - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 70)
    
    # Check recent run folders
    cmd = [
        "docker", "exec", "astro-airflow_541364-scheduler-1", 
        "bash", "-c", 
        "ls -lt /usr/local/airflow/logs/dag_id=nyc_311_incremental_etl_azure/ | head -n 3"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print("\n📁 Recent DAG Runs:")
        print(result.stdout)
    except Exception as e:
        print(f"Error checking runs: {e}")
    
    # Check processed files in Azure
    print("\n📊 Checking processed files tracker...")
    try:
        with open('C:\\Users\\David Ibanga\\Data Engineering practicals\\Urban_Cities_live_Service\\astro-airflow\\include\\data\\adf_processed_files.json', 'r') as f:
            import json
            data = json.load(f)
            print(f"   Total files processed by ADF: {len(data.get('processed_files', []))}")
            if data.get('processed_files'):
                print(f"   Last processed: {data['processed_files'][-1]}")
    except Exception as e:
        print(f"   Could not read tracker: {e}")
    
    print("\n" + "=" * 70)
    print("\n✨ Next Steps:")
    print("   1. Open Airflow UI: http://localhost:8080")
    print("   2. Click on 'nyc_311_incremental_etl_azure' DAG")
    print("   3. View the Grid view to see task progress")
    print("   4. Click on tasks to see logs")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    check_latest_run()
