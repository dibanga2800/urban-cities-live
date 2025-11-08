"""
Quick SQL Database Check using Azure CLI
"""
import subprocess
import json

def run_sql_query(query):
    """Run SQL query using Azure CLI"""
    cmd = [
        "az", "sql", "db", "query",
        "--server", "urban-cities-sql-srv-2025",
        "--database", "urban_cities_db",
        "--query-text", query,
        "--output", "json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"Error: {result.stderr}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

print("=" * 80)
print("NYC 311 DATABASE QUICK CHECK")
print("=" * 80)

# Query 1: Row count
print("\n1️⃣  Checking row count...")
query1 = "SELECT COUNT(*) as total_rows FROM nyc_311_requests;"
result = run_sql_query(query1)
if result:
    print(f"   Total Rows: {result}")

# Query 2: Recent records
print("\n2️⃣  Checking recent records...")
query2 = """
SELECT TOP 3 
    unique_key, 
    created_date, 
    closed_date,
    resolution_hours,
    is_closed,
    processed_at
FROM nyc_311_requests 
ORDER BY processed_at DESC;
"""
result = run_sql_query(query2)
if result:
    print(f"   Recent Records: {json.dumps(result, indent=2)}")

# Query 3: Column stats
print("\n3️⃣  Checking column completeness...")
query3 = """
SELECT 
    COUNT(closed_date) as closed_date_count,
    COUNT(resolution_hours) as resolution_hours_count,
    AVG(data_quality_score) as avg_quality
FROM nyc_311_requests;
"""
result = run_sql_query(query3)
if result:
    print(f"   Column Stats: {json.dumps(result, indent=2)}")

print("\n" + "=" * 80)
print("✅ If you see data above, the pipeline is working correctly!")
print("=" * 80)
