import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=urban-cities-sql-srv-2025x.database.windows.net;'
    'DATABASE=urban_cities_db;'
    'UID=sqladmin;'
    'PWD=D030avbang@@'
)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'nyc_311_requests'")
table_exists = cursor.fetchone()[0] == 1
cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'nyc_311_requests'")
column_count = cursor.fetchone()[0]
print(f"Table exists: {table_exists}")
print(f"Column count: {column_count}")
conn.close()
