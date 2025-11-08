import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=urban-cities-sql-srv-2025x.database.windows.net;'
    'DATABASE=urban_cities_db;'
    'UID=sqladmin;'
    'PWD=D030avbang@@'
)
cursor = conn.cursor()

# Count total rows
cursor.execute("SELECT COUNT(*) FROM dbo.nyc_311_requests")
row_count = cursor.fetchone()[0]
print(f"Total rows in nyc_311_requests: {row_count}")

# Get sample data
cursor.execute("""
    SELECT TOP 5 
        unique_key, 
        created_date, 
        agency, 
        complaint_type, 
        borough,
        status
    FROM dbo.nyc_311_requests 
    ORDER BY created_date DESC
""")
print("\nSample records (most recent):")
print("-" * 80)
for row in cursor.fetchall():
    print(f"Key: {row[0]}, Date: {row[1]}, Agency: {row[2]}, Type: {row[3]}, Borough: {row[4]}, Status: {row[5]}")

# Get summary statistics
cursor.execute("""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT agency) as agencies,
        COUNT(DISTINCT complaint_type) as complaint_types,
        MIN(created_date) as earliest_date,
        MAX(created_date) as latest_date
    FROM dbo.nyc_311_requests
""")
stats = cursor.fetchone()
print("\n" + "=" * 80)
print("DATA SUMMARY")
print("=" * 80)
print(f"Total Records: {stats[0]:,}")
print(f"Unique Agencies: {stats[1]}")
print(f"Unique Complaint Types: {stats[2]}")
print(f"Date Range: {stats[3]} to {stats[4]}")
print("=" * 80)

conn.close()
