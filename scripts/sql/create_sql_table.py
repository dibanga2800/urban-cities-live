"""
Create SQL Table Schema for NYC 311 Data
Creates the target table in Azure SQL Database
"""
import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_sql_table():
    """Create the nyc_311_requests table in Azure SQL Database"""
    
    print("\n" + "="*60)
    print("  AZURE SQL TABLE CREATION")
    print("="*60 + "\n")
    
    # Get SQL credentials
    server = os.getenv('SQL_SERVER')
    database = os.getenv('SQL_DATABASE')
    username = os.getenv('SQL_USERNAME')
    password = os.getenv('SQL_PASSWORD')
    
    print(f"Configuration:")
    print(f"  • Server: {server}")
    print(f"  • Database: {database}")
    print(f"  • Username: {username}\n")
    
    # Connection string
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password}"
    )
    
    # SQL CREATE TABLE statement
    create_table_sql = """
    -- Drop table if exists (for testing)
    IF OBJECT_ID('dbo.nyc_311_requests', 'U') IS NOT NULL
        DROP TABLE dbo.nyc_311_requests;
    
    -- Create the table
    CREATE TABLE dbo.nyc_311_requests (
        unique_key VARCHAR(50) PRIMARY KEY,
        created_date DATETIME NOT NULL,
        closed_date DATETIME,
        agency VARCHAR(50),
        agency_name VARCHAR(200),
        complaint_type VARCHAR(100),
        descriptor VARCHAR(200),
        location_type VARCHAR(100),
        incident_zip VARCHAR(10),
        incident_address VARCHAR(500),
        street_name VARCHAR(200),
        city VARCHAR(100),
        borough VARCHAR(50),
        latitude FLOAT,
        longitude FLOAT,
        location VARCHAR(100),
        status VARCHAR(50),
        
        -- Derived columns from transformation (matching Transformation.py output)
        created_year INT,
        created_month INT,
        created_day INT,
        created_hour INT,
        created_weekday VARCHAR(20),
        resolution_hours FLOAT,
        is_closed BIT,
        has_location BIT,
        processed_at DATETIME,
        data_quality_score FLOAT
    );
    
    -- Create indexes for common queries
    CREATE INDEX idx_created_date ON dbo.nyc_311_requests(created_date);
    CREATE INDEX idx_agency ON dbo.nyc_311_requests(agency);
    CREATE INDEX idx_complaint_type ON dbo.nyc_311_requests(complaint_type);
    CREATE INDEX idx_borough ON dbo.nyc_311_requests(borough);
    CREATE INDEX idx_status ON dbo.nyc_311_requests(status);
    CREATE INDEX idx_created_year_month ON dbo.nyc_311_requests(created_year, created_month);
    """
    
    try:
        print("Step 1: Connecting to Azure SQL Database...")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        print("   ✓ Connected successfully\n")
        
        print("Step 2: Creating table 'nyc_311_requests'...")
        cursor.execute(create_table_sql)
        conn.commit()
        print("   ✓ Table created successfully")
        print("   ✓ Indexes created successfully\n")
        
        # Verify table exists
        print("Step 3: Verifying table creation...")
        cursor.execute("""
            SELECT 
                TABLE_NAME,
                (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'nyc_311_requests') as ColumnCount
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'nyc_311_requests'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"   ✓ Table verified: {result[0]}")
            print(f"   ✓ Columns: {result[1]}\n")
        
        # List all columns
        print("Step 4: Table Schema:")
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
        
        columns = cursor.fetchall()
        print(f"   Total Columns: {len(columns)}")
        print("\n   Key Columns:")
        for col in columns[:10]:  # Show first 10
            col_name, data_type, max_len, nullable = col
            length = f"({max_len})" if max_len else ""
            print(f"     • {col_name}: {data_type}{length} {'NULL' if nullable == 'YES' else 'NOT NULL'}")
        
        if len(columns) > 10:
            print(f"     ... and {len(columns) - 10} more columns")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("  ✓ SQL TABLE SETUP COMPLETED!")
        print("="*60)
        print("\nTable Details:")
        print(f"  • Name: nyc_311_requests")
        print(f"  • Columns: {len(columns)}")
        print(f"  • Primary Key: unique_key")
        print(f"  • Indexes: 6 indexes created")
        print("\nNext Steps:")
        print("  1. Run test_etl_pipeline.py to load data to ADLS")
        print("  2. Trigger ADF pipeline to copy to SQL")
        print("  3. Query the table to verify data")
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
        success = create_sql_table()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Table creation failed: {str(e)}")
        exit(1)
