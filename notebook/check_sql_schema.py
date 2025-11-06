import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={os.getenv('SQL_SERVER')};"
    f"DATABASE={os.getenv('SQL_DATABASE')};"
    f"UID={os.getenv('SQL_USERNAME')};"
    f"PWD={os.getenv('SQL_PASSWORD')}"
)

cursor = conn.cursor()
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME='nyc_311_requests' 
    AND COLUMN_NAME IN ('created_date', 'closed_date', 'processed_at')
""")

print('=== DATETIME COLUMN SCHEMA ===')
for row in cursor:
    print(f'{row[0]}: {row[1]} (nullable: {row[2]})')

conn.close()
