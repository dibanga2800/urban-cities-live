import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

server = os.getenv('SQL_SERVER')
database = os.getenv('SQL_DATABASE')
username = os.getenv('SQL_USERNAME')
password = os.getenv('SQL_PASSWORD')

conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = cursor.fetchall()
    
    print(f"Database: {database}")
    print(f"Server: {server}")
    print(f"\nTables found: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")
    
    # If nyc_311_requests exists, show row count
    if any('nyc_311_requests' in str(t[0]) for t in tables):
        cursor.execute("SELECT COUNT(*) FROM nyc_311_requests")
        count = cursor.fetchone()[0]
        print(f"\nTable 'nyc_311_requests' has {count} rows")
    
    cursor.close()
    conn.close()
    print("\nConnection successful!")
    
except Exception as e:
    print(f"Error: {e}")
