"""
Verify data in Azure SQL Database
"""
import pyodbc
import sys

# Configuration
server = 'urban-cities-sql-server.database.windows.net'
database = 'urban_cities_db'
username = 'sqladmin'
password = 'D030avbang@@'

print("=" * 70)
print("  VERIFY SQL DATABASE DATA")
print("=" * 70)
print(f"Server: {server}")
print(f"Database: {database}\n")

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
    
    # Check total records
    print("QUERY 1: Total Record Count")
    print("-" * 70)
    cursor.execute("SELECT COUNT(*) as total_records FROM dbo.nyc_311_requests")
    row = cursor.fetchone()
    print(f"Total records in database: {row[0]}\n")
    
    # Check test records
    print("QUERY 2: Test Records (TEST001, TEST002, TEST003)")
    print("-" * 70)
    cursor.execute("""
        SELECT 
            unique_key,
            agency,
            complaint_type,
            borough,
            created_year,
            created_month,
            created_day,
            created_weekday,
            resolution_hours,
            has_location,
            is_closed,
            data_quality_score,
            load_timestamp
        FROM dbo.nyc_311_requests 
        WHERE unique_key IN ('TEST001', 'TEST002', 'TEST003')
        ORDER BY unique_key
    """)
    
    rows = cursor.fetchall()
    if rows:
        print(f"Found {len(rows)} test record(s):\n")
        for row in rows:
            print(f"  Unique Key: {row[0]}")
            print(f"  Agency: {row[1]}")
            print(f"  Complaint: {row[2]}")
            print(f"  Borough: {row[3]}")
            print(f"  Created: {row[4]}-{row[5]:02d}-{row[6]:02d} ({row[7]})")
            print(f"  Resolution Hours: {row[8]}")
            print(f"  Has Location: {row[9]}")
            print(f"  Is Closed: {row[10]}")
            print(f"  Quality Score: {row[11]}")
            print(f"  Load Timestamp: {row[12]}")
            print()
    else:
        print("No test records found.\n")
    
    # Check most recent records
    print("QUERY 3: Most Recent 5 Records")
    print("-" * 70)
    cursor.execute("""
        SELECT TOP 5
            unique_key,
            agency,
            complaint_type,
            created_year,
            created_month,
            created_day,
            load_timestamp
        FROM dbo.nyc_311_requests 
        ORDER BY load_timestamp DESC
    """)
    
    rows = cursor.fetchall()
    print(f"Found {len(rows)} recent record(s):\n")
    for i, row in enumerate(rows, 1):
        print(f"  {i}. {row[0]} | {row[1]} | {row[2]} | {row[3]}-{row[4]:02d}-{row[6]:02d} | {row[6]}")
    
    # Check schema
    print("\n" + "=" * 70)
    print("QUERY 4: Table Schema (All Columns)")
    print("=" * 70)
    cursor.execute("""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'nyc_311_requests'
        ORDER BY ORDINAL_POSITION
    """)
    
    rows = cursor.fetchall()
    print(f"\nTable has {len(rows)} columns:\n")
    for row in rows:
        col_name = row[0]
        data_type = row[1]
        max_length = f"({row[2]})" if row[2] else ""
        nullable = "NULL" if row[3] == 'YES' else "NOT NULL"
        print(f"  • {col_name:30} {data_type}{max_length:15} {nullable}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("  ✓ VERIFICATION COMPLETED!")
    print("=" * 70)
    
except pyodbc.Error as e:
    print(f"\n✗ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
    sys.exit(1)
