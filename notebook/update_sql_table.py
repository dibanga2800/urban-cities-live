"""
Update SQL Table Schema to Match Transformation Output
Adds the created_weekday column
"""
import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_sql_table():
    """Update the nyc_311_requests table schema"""
    
    print("\n" + "="*60)
    print("  UPDATE SQL TABLE SCHEMA")
    print("="*60 + "\n")
    
    # Get SQL credentials
    server = os.getenv('SQL_SERVER')
    database = os.getenv('SQL_DATABASE')
    username = os.getenv('SQL_USERNAME')
    password = os.getenv('SQL_PASSWORD')
    
    print(f"Configuration:")
    print(f"  • Server: {server}")
    print(f"  • Database: {database}\n")
    
    # Connection string
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password}"
    )
    
    # SQL ALTER TABLE statement
    alter_table_sql = """
    -- Add created_weekday column if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[nyc_311_requests]') AND name = 'created_weekday')
    BEGIN
        ALTER TABLE dbo.nyc_311_requests
        ADD created_weekday VARCHAR(20);
        PRINT 'Added created_weekday column';
    END
    
    -- Add resolution_hours column if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[nyc_311_requests]') AND name = 'resolution_hours')
    BEGIN
        ALTER TABLE dbo.nyc_311_requests
        ADD resolution_hours FLOAT;
        PRINT 'Added resolution_hours column';
    END
    
    -- Add processed_at column if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[nyc_311_requests]') AND name = 'processed_at')
    BEGIN
        ALTER TABLE dbo.nyc_311_requests
        ADD processed_at DATETIME;
        PRINT 'Added processed_at column';
    END
    """
    
    try:
        print("Step 1: Connecting to Azure SQL Database...")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        print("   ✓ Connected successfully\n")
        
        print("Step 2: Adding created_weekday column...")
        cursor.execute(alter_table_sql)
        conn.commit()
        print("   ✓ Column added successfully\n")
        
        # Verify column exists
        print("Step 3: Verifying schema update...")
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'nyc_311_requests' AND COLUMN_NAME = 'created_weekday'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"   ✓ Column verified: {result[0]} ({result[1]}({result[2]}))")
        else:
            print("   ⚠ Column not found")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("  ✓ SCHEMA UPDATE COMPLETED!")
        print("="*60 + "\n")
        
        return True
        
    except pyodbc.Error as e:
        print(f"\n✗ SQL Error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = update_sql_table()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Update failed: {str(e)}")
        exit(1)
