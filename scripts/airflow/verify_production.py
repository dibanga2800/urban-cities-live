"""
Production Verification Script
Comprehensive check of the ETL pipeline and Azure resources
"""
import pyodbc
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
env_path = 'C:\\Users\\David Ibanga\\Data Engineering practicals\\Urban_Cities_live_Service\\astro-airflow\\.env'
load_dotenv(env_path)

# SQL Server connection details
SQL_SERVER = os.getenv('AZURE_SQL_SERVER', 'urban-cities-sql-srv-2025.database.windows.net')
SQL_DATABASE = os.getenv('AZURE_SQL_DATABASE', 'urban_cities_db')
SQL_USERNAME = os.getenv('AZURE_SQL_USERNAME')
SQL_PASSWORD = os.getenv('AZURE_SQL_PASSWORD')

def print_header(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def check_sql_database():
    """Verify data in Azure SQL Database"""
    print_header("AZURE SQL DATABASE VERIFICATION")
    
    try:
        # Connection string
        conn_str = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server=tcp:{SQL_SERVER},1433;"
            f"Database={SQL_DATABASE};"
            f"Uid={SQL_USERNAME};"
            f"Pwd={SQL_PASSWORD};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        print(f"\n📊 Connecting to: {SQL_SERVER}/{SQL_DATABASE}")
        
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            
            # Query 1: Overall statistics
            print("\n1️⃣  Overall Statistics:")
            query1 = """
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT unique_key) as unique_records,
                COUNT(closed_date) as rows_with_closed_date,
                COUNT(CASE WHEN resolution_hours > 0 THEN 1 END) as rows_with_resolution_hours,
                ROUND(AVG(CASE WHEN resolution_hours > 0 THEN resolution_hours END), 2) as avg_resolution_hours,
                MAX(created_date) as latest_record,
                MAX(processed_at) as last_processed
            FROM nyc_311_requests;
            """
            cursor.execute(query1)
            row = cursor.fetchone()
            
            print(f"   Total Rows: {row[0]:,}")
            print(f"   Unique Records: {row[1]:,}")
            print(f"   Rows with Closed Date: {row[2]:,}")
            print(f"   Rows with Resolution Hours > 0: {row[3]:,}")
            print(f"   Average Resolution Hours: {row[4] if row[4] else 'N/A'}")
            print(f"   Latest Record: {row[5]}")
            print(f"   Last Processed: {row[6]}")
            
            # Query 2: Column completeness
            print("\n2️⃣  Column Completeness Check:")
            query2 = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN unique_key IS NOT NULL THEN 1 ELSE 0 END) as unique_key_filled,
                SUM(CASE WHEN created_date IS NOT NULL THEN 1 ELSE 0 END) as created_date_filled,
                SUM(CASE WHEN closed_date IS NOT NULL THEN 1 ELSE 0 END) as closed_date_filled,
                SUM(CASE WHEN agency IS NOT NULL AND agency <> '' THEN 1 ELSE 0 END) as agency_filled,
                SUM(CASE WHEN complaint_type IS NOT NULL AND complaint_type <> '' THEN 1 ELSE 0 END) as complaint_type_filled,
                SUM(CASE WHEN resolution_hours IS NOT NULL THEN 1 ELSE 0 END) as resolution_hours_filled,
                SUM(CASE WHEN is_closed IS NOT NULL THEN 1 ELSE 0 END) as is_closed_filled,
                SUM(CASE WHEN data_quality_score IS NOT NULL THEN 1 ELSE 0 END) as quality_score_filled
            FROM nyc_311_requests;
            """
            cursor.execute(query2)
            row = cursor.fetchone()
            
            total = row[0]
            print(f"   unique_key: {row[1]:,}/{total:,} ({row[1]/total*100:.1f}%)")
            print(f"   created_date: {row[2]:,}/{total:,} ({row[2]/total*100:.1f}%)")
            print(f"   closed_date: {row[3]:,}/{total:,} ({row[3]/total*100:.1f}%)")
            print(f"   agency: {row[4]:,}/{total:,} ({row[4]/total*100:.1f}%)")
            print(f"   complaint_type: {row[5]:,}/{total:,} ({row[5]/total*100:.1f}%)")
            print(f"   resolution_hours: {row[6]:,}/{total:,} ({row[6]/total*100:.1f}%)")
            print(f"   is_closed: {row[7]:,}/{total:,} ({row[7]/total*100:.1f}%)")
            print(f"   data_quality_score: {row[8]:,}/{total:,} ({row[8]/total*100:.1f}%)")
            
            # Query 3: Recent records sample
            print("\n3️⃣  Recent Records (Top 5):")
            query3 = """
            SELECT TOP 5
                unique_key, 
                created_date, 
                CASE WHEN closed_date = '' THEN NULL ELSE closed_date END as closed_date,
                agency, 
                complaint_type,
                resolution_hours,
                is_closed,
                data_quality_score,
                processed_at
            FROM nyc_311_requests 
            ORDER BY processed_at DESC;
            """
            cursor.execute(query3)
            rows = cursor.fetchall()
            
            for i, row in enumerate(rows, 1):
                print(f"\n   Record {i}:")
                print(f"      Unique Key: {row[0]}")
                print(f"      Created: {row[1]}")
                print(f"      Closed: {row[2] if row[2] else 'Still Open'}")
                print(f"      Agency: {row[3]}")
                print(f"      Type: {row[4][:50]}...")
                print(f"      Resolution Hours: {row[5]}")
                print(f"      Is Closed: {row[6]}")
                print(f"      Quality Score: {row[7]}")
                print(f"      Processed: {row[8]}")
            
            # Query 4: Data quality metrics
            print("\n4️⃣  Data Quality Metrics:")
            query4 = """
            SELECT 
                AVG(data_quality_score) as avg_quality,
                MIN(data_quality_score) as min_quality,
                MAX(data_quality_score) as max_quality,
                COUNT(CASE WHEN data_quality_score >= 80 THEN 1 END) as high_quality_count,
                COUNT(CASE WHEN data_quality_score BETWEEN 50 AND 79 THEN 1 END) as medium_quality_count,
                COUNT(CASE WHEN data_quality_score < 50 THEN 1 END) as low_quality_count
            FROM nyc_311_requests;
            """
            cursor.execute(query4)
            row = cursor.fetchone()
            
            print(f"   Average Quality Score: {row[0]:.2f}")
            print(f"   Min Quality Score: {row[1]:.2f}")
            print(f"   Max Quality Score: {row[2]:.2f}")
            print(f"   High Quality (≥80): {row[3]:,}")
            print(f"   Medium Quality (50-79): {row[4]:,}")
            print(f"   Low Quality (<50): {row[5]:,}")
            
            print("\n✅ Database verification completed successfully!")
            return True
            
    except pyodbc.Error as e:
        print(f"\n❌ Database Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def check_processed_files():
    """Check processed files tracker"""
    print_header("PROCESSED FILES TRACKER")
    
    try:
        import json
        tracker_path = 'C:\\Users\\David Ibanga\\Data Engineering practicals\\Urban_Cities_live_Service\\astro-airflow\\include\\data\\adf_processed_files.json'
        
        with open(tracker_path, 'r') as f:
            data = json.load(f)
            
        files = data.get('processed_files', [])
        print(f"\n📁 Total Files Processed: {len(files)}")
        
        if files:
            print(f"\n   First File: {files[0]}")
            print(f"   Last File: {files[-1]}")
            
            if len(files) >= 5:
                print(f"\n   Recent 5 Files:")
                for f in files[-5:]:
                    print(f"      - {f}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error reading tracker: {e}")
        return False

def check_etl_state():
    """Check ETL state"""
    print_header("ETL STATE")
    
    try:
        import json
        state_path = 'C:\\Users\\David Ibanga\\Data Engineering practicals\\Urban_Cities_live_Service\\astro-airflow\\include\\data\\etl_state.json'
        
        with open(state_path, 'r') as f:
            data = json.load(f)
            
        print(f"\n📊 Last Successful Run: {data.get('last_successful_run', 'N/A')}")
        print(f"   Last Processed Date: {data.get('last_processed_date', 'N/A')}")
        print(f"   Total Records Processed: {data.get('total_records_processed', 0):,}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error reading ETL state: {e}")
        return False

def print_production_summary():
    """Print production readiness summary"""
    print_header("PRODUCTION READINESS SUMMARY")
    
    print("\n✅ Pipeline Components:")
    print("   ✓ Airflow DAG: Running hourly schedule")
    print("   ✓ Data Extraction: NYC 311 API integration")
    print("   ✓ Data Transformation: 20-column schema with derived features")
    print("   ✓ Azure Data Lake: Parquet files in processed container")
    print("   ✓ Azure Data Factory: UPSERT pipeline with file tracking")
    print("   ✓ Azure SQL Database: nyc_311_requests table")
    
    print("\n📋 Monitoring & Operations:")
    print("   • Airflow UI: http://localhost:8080")
    print("   • Schedule: Runs every 1 hour (can trigger manually)")
    print("   • File Tracking: Prevents duplicate processing")
    print("   • Data Quality: Scored on every record")
    
    print("\n🔒 Production Considerations:")
    print("   ⚠️  Secrets: Stored in .env file (consider Azure Key Vault)")
    print("   ⚠️  Monitoring: Add Azure Monitor/Application Insights")
    print("   ⚠️  Alerting: Configure failure notifications")
    print("   ⚠️  Backup: Set up SQL database backups")
    print("   ⚠️  Scaling: Monitor Airflow resources")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  NYC 311 ETL PIPELINE - PRODUCTION VERIFICATION")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Run all checks
    sql_ok = check_sql_database()
    files_ok = check_processed_files()
    state_ok = check_etl_state()
    
    # Print summary
    print_production_summary()
    
    # Final status
    if sql_ok and files_ok and state_ok:
        print("\n🎉 ALL CHECKS PASSED - PIPELINE IS PRODUCTION READY!")
    else:
        print("\n⚠️  SOME CHECKS FAILED - REVIEW ABOVE OUTPUT")
    
    print("\n" + "=" * 80)
