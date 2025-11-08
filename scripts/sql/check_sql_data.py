"""Quick script to check SQL data"""
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv('../../astro-airflow/.env')

conn_str = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={os.getenv('SQL_SERVER')};"
    f"DATABASE={os.getenv('SQL_DATABASE')};"
    f"UID={os.getenv('SQL_USERNAME')};"
    f"PWD={os.getenv('SQL_PASSWORD')}"
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'nyc_311_requests'
    """)
    table_exists = cursor.fetchone()[0]
    
    if table_exists:
        print("✓ Table 'nyc_311_requests' exists")
        
        # Get record count
        cursor.execute('SELECT COUNT(*) FROM nyc_311_requests')
        count = cursor.fetchone()[0]
        print(f"✓ Total records: {count}")
        
        if count > 0:
            # Get latest record
            cursor.execute("""
                SELECT TOP 1 created_date, agency, complaint_type, borough 
                FROM nyc_311_requests 
                ORDER BY created_date DESC
            """)
            row = cursor.fetchone()
            print(f"✓ Latest record: {row[0]} | {row[1]} | {row[2]} | {row[3]}")
            
            # Get date range
            cursor.execute("""
                SELECT MIN(created_date) as earliest, MAX(created_date) as latest 
                FROM nyc_311_requests
            """)
            date_range = cursor.fetchone()
            print(f"✓ Date range: {date_range[0]} to {date_range[1]}")
            
            # Get agency breakdown
            cursor.execute("""
                SELECT TOP 5 agency, COUNT(*) as count 
                FROM nyc_311_requests 
                GROUP BY agency 
                ORDER BY count DESC
            """)
            print("\n✓ Top 5 agencies:")
            for row in cursor.fetchall():
                print(f"  - {row[0]}: {row[1]} requests")
    else:
        print("✗ Table 'nyc_311_requests' does not exist")
    
    conn.close()
    print("\n✓ SQL verification complete!")
    
except Exception as e:
    print(f"✗ Error: {e}")
