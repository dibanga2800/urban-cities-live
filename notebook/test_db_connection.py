import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables explicitly
load_dotenv()

server = os.getenv('SQL_SERVER')
database = os.getenv('SQL_DATABASE')
username = os.getenv('SQL_USERNAME')
password = os.getenv('SQL_PASSWORD')

print(f'Server: {server}')
print(f'Database: {database}')
print(f'Username: {username}')
print(f'Password: {"***" if password else "None"}')

if server and database and username and password:
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Check tables
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tables = cursor.fetchall()
        print(f'\nTables found: {len(tables)}')
        for table in tables:
            print(f'  - {table[0]}')

        # Check row count
        cursor.execute('SELECT COUNT(*) FROM nyc_311_requests')
        count = cursor.fetchone()[0]
        print(f'\nnyc_311_requests row count: {count}')

        # Try to get a sample row
        cursor.execute('SELECT TOP 1 * FROM nyc_311_requests')
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        print(f'\nColumns: {columns}')
        print(f'Sample row: {row}')

        cursor.close()
        conn.close()
        print('\nConnection successful!')
    except Exception as e:
        print(f'Connection error: {e}')
        import traceback
        traceback.print_exc()
else:
    print('Missing environment variables')