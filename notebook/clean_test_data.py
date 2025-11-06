"""
Clean test data from SQL Database
"""
import pyodbc
import sys

# Configuration
server = 'urban-cities-sql-server.database.windows.net'
database = 'urban_cities_db'
username = 'sqladmin'
password = 'D030avbang@@'

print("=" * 70)
print("  CLEAN TEST DATA")
print("=" * 70)

try:
    # Connection string
    conn_str = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password};'
        f'Encrypt=yes;'
        f'TrustServerCertificate=no;'
        f'Connection Timeout=30;'
    )
    
    print("Connecting to database...")
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    print("✓ Connected successfully\n")
    
    # Delete test records
    print("Deleting test records (TEST001, TEST002, TEST003)...")
    cursor.execute("""
        DELETE FROM dbo.nyc_311_requests 
        WHERE unique_key IN ('TEST001', 'TEST002', 'TEST003')
    """)
    
    rows_deleted = cursor.rowcount
    conn.commit()
    
    print(f"✓ Deleted {rows_deleted} test record(s)\n")
    
    # Verify deletion
    cursor.execute("""
        SELECT COUNT(*) FROM dbo.nyc_311_requests 
        WHERE unique_key IN ('TEST001', 'TEST002', 'TEST003')
    """)
    remaining = cursor.fetchone()[0]
    
    if remaining == 0:
        print("✓ All test records successfully removed")
    else:
        print(f"⚠ Warning: {remaining} test record(s) still exist")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("  ✓ CLEANUP COMPLETED!")
    print("=" * 70)
    
except pyodbc.Error as e:
    print(f"\n✗ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
    sys.exit(1)
