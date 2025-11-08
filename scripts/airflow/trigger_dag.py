"""
Trigger Airflow DAG via API
"""
import requests
import json
from datetime import datetime

# Airflow configuration
AIRFLOW_URL = "http://localhost:8080"
USERNAME = "admin"
PASSWORD = "admin"
DAG_ID = "nyc_311_incremental_etl_azure"

print("=" * 70)
print("  TRIGGER AIRFLOW DAG")
print("=" * 70)
print(f"DAG ID: {DAG_ID}")
print(f"URL: {AIRFLOW_URL}\n")

try:
    # Create session
    session = requests.Session()
    session.auth = (USERNAME, PASSWORD)
    
    # Trigger DAG
    trigger_url = f"{AIRFLOW_URL}/api/v1/dags/{DAG_ID}/dagRuns"
    
    payload = {
        "conf": {},
        "execution_date": datetime.utcnow().isoformat() + "Z"
    }
    
    print("Triggering DAG...")
    response = session.post(
        trigger_url,
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✓ DAG triggered successfully!")
        print(f"  Run ID: {result.get('dag_run_id')}")
        print(f"  State: {result.get('state')}")
        print(f"  Execution Date: {result.get('execution_date')}")
        print(f"\nView in UI: {AIRFLOW_URL}/dags/{DAG_ID}/grid")
    else:
        print(f"✗ Failed to trigger DAG")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.text}")
    
    print("\n" + "=" * 70)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
