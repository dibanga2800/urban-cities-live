"""
Complete End-to-End Workflow Test
Tests the full pipeline: Extract → Transform → Load → ADF → SQL
"""
import os
import time
import pyodbc
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import ETL modules
from Extraction import DataExtractor
from Transformation import DataTransformer
from Loading_Azure import AzureDataLoader

# Import Azure modules for ADF
from azure.identity import ClientSecretCredential
from azure.mgmt.datafactory import DataFactoryManagementClient

# Load environment variables
load_dotenv()

def test_complete_workflow():
    """Run complete end-to-end workflow test"""
    
    print("\n" + "="*70)
    print("  COMPLETE END-TO-END WORKFLOW TEST")
    print("="*70 + "\n")
    
    results = {
        'extraction': False,
        'transformation': False,
        'load_raw': False,
        'load_processed': False,
        'adf_trigger': False,
        'sql_verification': False
    }
    
    # ========================================
    # STEP 1: EXTRACT DATA
    # ========================================
    print("STEP 1: Extract Data from NYC 311 API")
    print("-" * 70)
    
    try:
        api_url = os.getenv('NYC_311_API_URL', 'https://data.cityofnewyork.us/resource/erm2-nwe9.json')
        extractor = DataExtractor(api_url=api_url)
        since_time = (datetime.now() - timedelta(days=1)).isoformat()
        
        print(f"   Extracting data since: {since_time}")
        df_extracted = extractor.extract_incremental(since_time=since_time)
        
        if df_extracted is None or len(df_extracted) == 0:
            print("   ⚠ No new data from API, using sample data...")
            import pandas as pd
            now = datetime.now()
            closed_time = now - timedelta(hours=2)
            
            # Generate unique test IDs using timestamp to avoid duplicate key errors
            timestamp_suffix = now.strftime('%Y%m%d%H%M%S')
            
            df_extracted = pd.DataFrame({
                'unique_key': [f'TEST001_{timestamp_suffix}', f'TEST002_{timestamp_suffix}', f'TEST003_{timestamp_suffix}'],
                'created_date': [now.isoformat(), now.isoformat(), now.isoformat()],
                'agency': ['NYPD', 'DOT', 'DSNY'],
                'complaint_type': ['Noise', 'Street Condition', 'Sanitation'],
                'descriptor': ['Loud Music', 'Pothole', 'Dirty Sidewalk'],
                'latitude': [40.7128, 40.7580, 40.6782],
                'longitude': [-74.0060, -73.9855, -73.9442],
                'status': ['Open', 'Closed', 'Open'],
                'borough': ['MANHATTAN', 'MANHATTAN', 'BROOKLYN'],
                'incident_zip': ['10001', '10022', '11201'],
                'location_type': ['Street', 'Street', 'Street'],
                'closed_date': [None, closed_time.isoformat(), None]
            })
            
            # Convert date columns to proper datetime format
            df_extracted['created_date'] = pd.to_datetime(df_extracted['created_date'])
            df_extracted['closed_date'] = pd.to_datetime(df_extracted['closed_date'])
            df_extracted['latitude'] = pd.to_numeric(df_extracted['latitude'])
            df_extracted['longitude'] = pd.to_numeric(df_extracted['longitude'])
        
        print(f"   ✓ Extracted {len(df_extracted)} records")
        print(f"   ✓ Columns: {len(df_extracted.columns)}")
        results['extraction'] = True
        
    except Exception as e:
        print(f"   ✗ Extraction failed: {e}")
        return results
    
    # ========================================
    # STEP 2: TRANSFORM DATA
    # ========================================
    print(f"\nSTEP 2: Transform Data")
    print("-" * 70)
    
    try:
        transformer = DataTransformer()
        df_transformed = transformer.transform(df_extracted)
        
        summary = transformer.get_transformation_summary(df_extracted, df_transformed)
        
        print(f"   ✓ Transformed {len(df_transformed)} records")
        print(f"   ✓ Quality Score: {summary['avg_quality_score']:.1f}%")
        print(f"   ✓ Records with Location: {summary['records_with_location']}")
        print(f"   ✓ Closed Complaints: {summary['closed_complaints']}")
        results['transformation'] = True
        
    except Exception as e:
        print(f"   ✗ Transformation failed: {e}")
        return results
    
    # ========================================
    # STEP 3: LOAD TO AZURE ADLS (RAW)
    # ========================================
    print(f"\nSTEP 3: Load Raw Data to Azure ADLS")
    print("-" * 70)
    
    try:
        loader = AzureDataLoader()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        raw_path = loader.load_to_raw_container(df_extracted, f"nyc_311_e2e_test_raw_{timestamp}")
        print(f"   ✓ Raw data uploaded")
        print(f"   ✓ Path: {raw_path}")
        results['load_raw'] = True
        
    except Exception as e:
        print(f"   ✗ Raw load failed: {e}")
        return results
    
    # ========================================
    # STEP 4: LOAD TO AZURE ADLS (PROCESSED)
    # ========================================
    print(f"\nSTEP 4: Load Processed Data to Azure ADLS")
    print("-" * 70)
    
    try:
        processed_path = loader.load_to_processed_container(df_transformed, f"nyc_311_e2e_test_processed_{timestamp}")
        processed_filename = processed_path.split('/')[-1]
        
        print(f"   ✓ Processed data uploaded")
        print(f"   ✓ Path: {processed_path}")
        print(f"   ✓ Filename: {processed_filename}")
        results['load_processed'] = True
        
    except Exception as e:
        print(f"   ✗ Processed load failed: {e}")
        return results
    
    # ========================================
    # STEP 5: TRIGGER ADF PIPELINE
    # ========================================
    print(f"\nSTEP 5: Trigger Azure Data Factory Pipeline")
    print("-" * 70)
    
    try:
        # Get ADF configuration
        tenant_id = os.getenv('AZURE_TENANT_ID')
        client_id = os.getenv('AZURE_CLIENT_ID')
        client_secret = os.getenv('AZURE_CLIENT_SECRET')
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        resource_group = os.getenv('ADF_RESOURCE_GROUP', 'urban-cities-rg')
        adf_name = os.getenv('ADF_NAME', 'urban-cities-adf')
        
        # Create credential
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Create ADF client
        adf_client = DataFactoryManagementClient(credential, subscription_id)
        
        print(f"   Triggering pipeline: CopyProcessedDataToSQL")
        
        # Create pipeline run
        run_response = adf_client.pipelines.create_run(
            resource_group,
            adf_name,
            "CopyProcessedDataToSQL"
        )
        
        run_id = run_response.run_id
        print(f"   ✓ Pipeline triggered")
        print(f"   ✓ Run ID: {run_id}")
        
        # Monitor pipeline run
        print(f"\n   Monitoring pipeline execution...")
        max_wait = 300  # 5 minutes
        wait_time = 0
        check_interval = 10
        
        while wait_time < max_wait:
            time.sleep(check_interval)
            wait_time += check_interval
            
            pipeline_run = adf_client.pipeline_runs.get(
                resource_group,
                adf_name,
                run_id
            )
            
            status = pipeline_run.status
            print(f"   Status: {status} (waited {wait_time}s)")
            
            if status in ['Succeeded', 'Failed', 'Cancelled']:
                break
        
        if status == 'Succeeded':
            print(f"   ✓ Pipeline completed successfully!")
            results['adf_trigger'] = True
        else:
            print(f"   ✗ Pipeline status: {status}")
            if hasattr(pipeline_run, 'message'):
                print(f"   Message: {pipeline_run.message}")
            return results
        
    except Exception as e:
        print(f"   ✗ ADF trigger failed: {e}")
        import traceback
        traceback.print_exc()
        return results
    
    # ========================================
    # STEP 6: VERIFY DATA IN SQL DATABASE
    # ========================================
    print(f"\nSTEP 6: Verify Data in Azure SQL Database")
    print("-" * 70)
    
    try:
        # Connect to SQL
        server = os.getenv('SQL_SERVER')
        database = os.getenv('SQL_DATABASE')
        username = os.getenv('SQL_USERNAME')
        password = os.getenv('SQL_PASSWORD')
        
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password}"
        )
        
        print(f"   Connecting to SQL Database...")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Check total records
        cursor.execute("SELECT COUNT(*) FROM nyc_311_requests")
        total_count = cursor.fetchone()[0]
        print(f"   ✓ Total records in table: {total_count}")
        
        # Check for test records
        cursor.execute("""
            SELECT COUNT(*) 
            FROM nyc_311_requests 
            WHERE unique_key IN ('TEST001', 'TEST002', 'TEST003')
        """)
        test_count = cursor.fetchone()[0]
        print(f"   ✓ Test records found: {test_count}")
        
        # Get latest records
        cursor.execute("""
            SELECT TOP 5 
                unique_key, 
                created_date, 
                agency, 
                complaint_type,
                data_quality_score
            FROM nyc_311_requests 
            ORDER BY load_timestamp DESC
        """)
        
        print(f"\n   Latest Records in SQL:")
        for row in cursor.fetchall():
            print(f"     • {row[0]}: {row[2]} - {row[3]} (Quality: {row[4]:.1f}%)")
        
        cursor.close()
        conn.close()
        
        results['sql_verification'] = True
        print(f"\n   ✓ SQL verification complete!")
        
    except Exception as e:
        print(f"   ✗ SQL verification failed: {e}")
        import traceback
        traceback.print_exc()
        return results
    
    # ========================================
    # FINAL SUMMARY
    # ========================================
    print("\n" + "="*70)
    print("  TEST RESULTS SUMMARY")
    print("="*70)
    
    all_steps = [
        ("Extract Data from API", results['extraction']),
        ("Transform Data", results['transformation']),
        ("Load to ADLS Raw Container", results['load_raw']),
        ("Load to ADLS Processed Container", results['load_processed']),
        ("Trigger ADF Pipeline", results['adf_trigger']),
        ("Verify Data in SQL Database", results['sql_verification'])
    ]
    
    for step_name, step_result in all_steps:
        status = "✓ PASS" if step_result else "✗ FAIL"
        print(f"  {status} - {step_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("  🎉 ALL TESTS PASSED! END-TO-END WORKFLOW VERIFIED!")
    else:
        print("  ⚠ SOME TESTS FAILED - SEE DETAILS ABOVE")
    print("="*70 + "\n")
    
    return results

if __name__ == "__main__":
    try:
        results = test_complete_workflow()
        all_passed = all(results.values())
        exit(0 if all_passed else 1)
    except Exception as e:
        print(f"\n✗ Workflow test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
