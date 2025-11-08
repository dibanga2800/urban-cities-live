"""
NYC 311 Incremental ETL Pipeline with Azure Integration
Airflow DAG for near real-time data processing with:
- Extract from NYC 311 API
- Transform/Clean data
- Load raw data to ADLS raw container
- Load processed data to ADLS processed container
- Trigger Azure Data Factory to copy processed data to SQL Database
"""

from datetime import datetime, timedelta
import os
import sys
import pandas as pd

# Astro project structure - include directory is available on Python path
from airflow import DAG
from airflow.operators.python import PythonOperator
try:
    from airflow.operators.dummy import DummyOperator as EmptyOperator
except ImportError:
    try:
        from airflow.operators.empty import EmptyOperator
    except ImportError:
        from airflow.operators.dummy_operator import DummyOperator as EmptyOperator

# Import ETL modules from include directory
from include.Extraction import DataExtractor
from include.Transformation import DataTransformer
from include.Loading_Azure import AzureDataLoader
import json

# State file for tracking last processed timestamp
# In Astro, /usr/local/airflow/include is mounted
STATE_FILE = '/usr/local/airflow/include/data/etl_state.json'
ADF_PROCESSED_FILES = '/usr/local/airflow/include/data/adf_processed_files.json'

def load_processed_files():
    """Load list of files already processed by ADF"""
    try:
        if os.path.exists(ADF_PROCESSED_FILES):
            with open(ADF_PROCESSED_FILES, 'r') as f:
                data = json.load(f)
                return set(data.get('processed_files', []))
    except Exception as e:
        print(f"Error loading processed files: {e}")
    return set()

def save_processed_files(processed_files_set):
    """Save list of files processed by ADF"""
    try:
        os.makedirs(os.path.dirname(ADF_PROCESSED_FILES), exist_ok=True)
        with open(ADF_PROCESSED_FILES, 'w') as f:
            json.dump({
                'processed_files': list(processed_files_set),
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)
        print(f"Processed files state saved: {len(processed_files_set)} files")
    except Exception as e:
        print(f"Error saving processed files: {e}")

def load_state():
    """Load last processed timestamp from state file"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                timestamp = state.get('last_processed_time')
                if timestamp:
                    # Ensure proper ISO 8601 format for Socrata API
                    # Remove milliseconds and use T separator
                    if '.' in timestamp:
                        timestamp = timestamp.split('.')[0]
                    if ' ' in timestamp:
                        timestamp = timestamp.replace(' ', 'T')
                    return timestamp
    except Exception as e:
        print(f"Error loading state: {e}")
    
    # Default to 24 hours ago if no state exists
    return (datetime.now() - timedelta(hours=24)).isoformat()

def save_state(timestamp):
    """Save last processed timestamp to state file"""
    try:
        # Ensure proper ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
        if '.' in timestamp:
            timestamp = timestamp.split('.')[0]
        if ' ' in timestamp:
            timestamp = timestamp.replace(' ', 'T')
            
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump({
                'last_processed_time': timestamp,
                'updated_at': datetime.now().isoformat()
            }, f, indent=2)
        print(f"State saved: {timestamp}")
    except Exception as e:
        print(f"Error saving state: {e}")

def extract_data(**context):
    """Extract data from NYC 311 API"""
    print("=" * 50)
    print("STEP 1: EXTRACTING DATA FROM NYC 311 API")
    print("=" * 50)
    
    # Get last processed time
    last_processed = load_state()
    print(f"Extracting data since: {last_processed}")
    
    # Configuration
    api_url = os.getenv("NYC_311_API_URL", "https://data.cityofnewyork.us/resource/erm2-nwe9.json")
    app_token = os.getenv("NYC_APP_TOKEN")
    batch_size = int(os.getenv("BATCH_SIZE", "1000"))
    
    # Initialize extractor
    extractor = DataExtractor(api_url=api_url, app_token=app_token, batch_size=batch_size)
    
    # Extract data
    df = extractor.extract_incremental(since_time=last_processed)
    
    print(f"Extracted {len(df)} records")
    print(f"Columns: {list(df.columns)}")
    
    if len(df) > 0:
        print(f"Date range: {df['created_date'].min()} to {df['created_date'].max()}")
    
    # Save to XCom
    context['task_instance'].xcom_push(key='raw_data_count', value=len(df))
    context['task_instance'].xcom_push(key='raw_data_columns', value=list(df.columns))
    
    # Save raw data to temporary file for next task
    output_dir = os.path.join('/usr/local/airflow/include', 'data', 'temp')
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_file = os.path.join(output_dir, f'raw_{timestamp}.csv')
    df.to_csv(raw_file, index=False)
    
    context['task_instance'].xcom_push(key='raw_file_path', value=raw_file)
    
    print(f"Raw data saved to: {raw_file}")
    print("=" * 50)
    
    return len(df)

def transform_data(**context):
    """Transform and clean the extracted data"""
    print("=" * 50)
    print("STEP 2: TRANSFORMING DATA")
    print("=" * 50)
    
    # Get raw data file path
    raw_file = context['task_instance'].xcom_pull(key='raw_file_path', task_ids='extract_data')
    
    if not raw_file or not os.path.exists(raw_file):
        print("No raw data file found - skipping transformation")
        return 0
    
    # Load raw data
    df = pd.read_csv(raw_file)
    print(f"Loaded {len(df)} records for transformation")
    
    # Initialize transformer
    transformer = DataTransformer()
    
    # Transform data
    transformed_df = transformer.transform(df)
    
    print(f"Transformed {len(transformed_df)} records")
    print(f"Columns after transformation: {list(transformed_df.columns)}")
    
    # Calculate data quality metrics from transformed data
    quality_metrics = {
        'raw_count': len(df),
        'processed_count': len(transformed_df),
        'avg_quality_score': transformed_df['data_quality_score'].mean() if 'data_quality_score' in transformed_df.columns else 0,
        'records_with_location': transformed_df['has_location'].sum() if 'has_location' in transformed_df.columns else 0
    }
    print(f"Data quality metrics: {quality_metrics}")
    
    # Save to XCom
    context['task_instance'].xcom_push(key='processed_data_count', value=len(transformed_df))
    context['task_instance'].xcom_push(key='quality_metrics', value=quality_metrics)
    
    # Pass the DataFrame directly through XCom using pickle serialization
    # This preserves string dtypes which are critical for datetime columns
    import pickle
    import base64
    
    pickled_data = pickle.dumps(transformed_df)
    encoded_data = base64.b64encode(pickled_data).decode('utf-8')
    context['task_instance'].xcom_push(key='processed_data_pickle', value=encoded_data)
    
    print(f"Processed data stored in XCom: {len(transformed_df)} records (preserved dtypes)")
    print("=" * 50)
    
    return len(transformed_df)

def load_to_azure(**context):
    """Load data to Azure Data Lake Storage"""
    print("=" * 50)
    print("STEP 3: LOADING DATA TO AZURE DATA LAKE")
    print("=" * 50)
    
    # Get file paths
    raw_file = context['task_instance'].xcom_pull(key='raw_file_path', task_ids='extract_data')
    # Get processed data from XCom instead of file
    processed_pickle = context['task_instance'].xcom_pull(key='processed_data_pickle', task_ids='transform_data')
    
    if not raw_file or not processed_pickle:
        print("No data files found - skipping load")
        return {'status': 'skipped'}
    
    # Load data
    raw_df = pd.read_csv(raw_file)
    
    # Deserialize processed DataFrame from pickle (preserves dtypes)
    import pickle
    import base64
    
    try:
        decoded_data = base64.b64decode(processed_pickle)
        processed_df = pickle.loads(decoded_data)
        print(f"Successfully deserialized processed data: {len(processed_df)} records")
        
        # Verify datetime column dtypes are preserved
        datetime_cols = ['created_date', 'closed_date', 'processed_at']
        for col in datetime_cols:
            if col in processed_df.columns:
                print(f"  {col}: dtype={processed_df[col].dtype}, sample={processed_df[col].iloc[0] if len(processed_df) > 0 else 'N/A'}")
                
    except Exception as e:
        print(f"Error deserializing processed data: {e}")
        return {'status': 'error', 'error': str(e)}
    
    print(f"Loading {len(raw_df)} raw records and {len(processed_df)} processed records to ADLS")
    
    # Initialize Azure loader
    loader = AzureDataLoader()
    
    # Load to ADLS raw container
    print("\nUploading to ADLS raw container...")
    raw_path = loader.load_to_raw_container(raw_df, file_prefix="nyc_311")
    
    # Load to ADLS processed container
    print("\nUploading to ADLS processed container...")
    processed_path = loader.load_to_processed_container(processed_df, file_prefix="nyc_311")
    
    # Save paths to XCom
    context['task_instance'].xcom_push(key='raw_adls_path', value=raw_path)
    context['task_instance'].xcom_push(key='processed_adls_path', value=processed_path)
    
    result = {
        'raw_path': raw_path,
        'processed_path': processed_path,
        'raw_records': len(raw_df),
        'processed_records': len(processed_df),
        'status': 'success' if (raw_path and processed_path) else 'partial'
    }
    
    print(f"\nAzure upload results: {result}")
    print("=" * 50)
    
    return result

def trigger_adf_pipeline(**context):
    """Trigger Azure Data Factory pipeline to copy ALL unprocessed files to SQL Database"""
    print("=" * 50)
    print("STEP 4: TRIGGERING AZURE DATA FACTORY PIPELINE")
    print("=" * 50)
    
    # Get the latest processed file path from this run
    latest_processed_path = context['task_instance'].xcom_pull(key='processed_adls_path', task_ids='load_to_azure')
    
    # Load tracking state - which files have already been processed
    already_processed = load_processed_files()
    print(f"\nAlready processed files: {len(already_processed)}")
    
    # Initialize Azure loader
    loader = AzureDataLoader()
    
    # Get ALL parquet files from processed container
    try:
        from azure.storage.filedatalake import DataLakeServiceClient
        
        fs = loader.datalake_client.get_file_system_client(loader.processed_container)
        paths = list(fs.get_paths(path="processed-data"))
        parquet_files = [p for p in paths if (not p.is_directory and p.name.endswith('.parquet'))]
        parquet_files.sort(key=lambda p: p.last_modified)  # Oldest first
        
        # Filter out already processed files
        files_to_process = [pf for pf in parquet_files if os.path.basename(pf.name) not in already_processed]
        
        print(f"\nTotal parquet files in container: {len(parquet_files)}")
        print(f"Already processed: {len(already_processed)}")
        print(f"New files to process: {len(files_to_process)}")
        
        if files_to_process:
            print("\nFiles to process:")
            for pf in files_to_process:
                file_name = os.path.basename(pf.name)
                print(f"  - {file_name} (modified: {pf.last_modified})")
        
        if not files_to_process:
            print("\nNo new files to process - all files already loaded to SQL")
            return {'status': 'skipped', 'message': 'All files already processed'}
        
        # Process each file through ADF
        results = []
        successful = 0
        failed = 0
        newly_processed = set(already_processed)
        
        for pf in files_to_process:
            file_name = os.path.basename(pf.name)
            file_path = f"abfss://{loader.processed_container}@{loader.storage_account}.dfs.core.windows.net/{pf.name}"
            
            print(f"\n▶ Processing file: {file_name}")
            
            # Trigger ADF pipeline for this file
            adf_result = loader.trigger_adf_pipeline(
                pipeline_name="CopyProcessedDataToSQL",
                source_file_path=file_path
            )
            
            results.append({
                'file': file_name,
                'run_id': adf_result.get('run_id'),
                'status': adf_result.get('status'),
                'duration_ms': adf_result.get('duration_ms')
            })
            
            if adf_result.get('status') == 'Succeeded':
                successful += 1
                newly_processed.add(file_name)
                print(f"  ✓ Success: {file_name}")
            else:
                failed += 1
                print(f"  ✗ Failed: {file_name} - {adf_result.get('message', 'Unknown error')}")
        
        # Save updated processed files list
        save_processed_files(newly_processed)
        
        # Summary
        print(f"\n{'=' * 50}")
        print(f"ADF Pipeline Batch Results:")
        print(f"  Total Files Processed: {len(files_to_process)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total Tracked: {len(newly_processed)}")
        print(f"{'=' * 50}")
        
        # Store results in XCom
        context['task_instance'].xcom_push(key='adf_results', value=results)
        context['task_instance'].xcom_push(key='adf_status', value='Succeeded' if failed == 0 else 'Partial')
        
        return {
            'status': 'Succeeded' if failed == 0 else 'Partial',
            'total_files': len(files_to_process),
            'successful': successful,
            'failed': failed,
            'results': results
        }
        
    except Exception as e:
        print(f"Error processing files: {e}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'Error',
            'message': str(e)
        }

def update_state(**context):
    """Update ETL state with latest processed timestamp"""
    print("=" * 50)
    print("STEP 5: UPDATING ETL STATE")
    print("=" * 50)
    
    # Get processed data from XCom
    processed_pickle = context['task_instance'].xcom_pull(key='processed_data_pickle', task_ids='transform_data')
    
    if processed_pickle:
        # Deserialize DataFrame from pickle
        import pickle
        import base64
        
        try:
            decoded_data = base64.b64decode(processed_pickle)
            df = pickle.loads(decoded_data)
            
            if len(df) > 0 and 'created_date' in df.columns:
                latest_timestamp = df['created_date'].max()
                save_state(latest_timestamp)
                print(f"State updated with timestamp: {latest_timestamp}")
            else:
                print("No data to update state")
        except Exception as e:
            print(f"Error deserializing data for state update: {e}")
    else:
        print("No processed data found - state not updated")
    
    print("=" * 50)

def cleanup_temp_files(**context):
    """Clean up temporary files"""
    print("Cleaning up temporary files...")
    
    raw_file = context['task_instance'].xcom_pull(key='raw_file_path', task_ids='extract_data')
    # No processed_file to clean up since we're using XCom now
    
    for file_path in [raw_file]:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

def send_notification(**context):
    """Send completion notification with metrics"""
    print("=" * 50)
    print("ETL PIPELINE COMPLETED")
    print("=" * 50)
    
    # Gather metrics
    raw_count = context['task_instance'].xcom_pull(key='raw_data_count', task_ids='extract_data')
    processed_count = context['task_instance'].xcom_pull(key='processed_data_count', task_ids='transform_data')
    quality_metrics = context['task_instance'].xcom_pull(key='quality_metrics', task_ids='transform_data')
    adf_status = context['task_instance'].xcom_pull(key='adf_status', task_ids='trigger_adf_pipeline')
    
    print(f"\nPipeline Metrics:")
    print(f"  Records Extracted: {raw_count}")
    print(f"  Records Processed: {processed_count}")
    print(f"  Data Quality Score: {quality_metrics.get('quality_score', 'N/A') if quality_metrics else 'N/A'}")
    print(f"  ADF Pipeline Status: {adf_status}")
    print(f"  Execution Time: {context['execution_date']}")
    
    print("=" * 50)
    
    # TODO: Add email/Slack notification here
    return {
        'status': 'success',
        'raw_count': raw_count,
        'processed_count': processed_count,
        'adf_status': adf_status
    }

# Define DAG
default_args = {
    'owner': 'data-engineering-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 4),  # Yesterday's date
    'email': ['your-email@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30)
}

dag = DAG(
    'nyc_311_incremental_etl_azure',
    default_args=default_args,
    description='NYC 311 Incremental ETL with Azure Data Lake and ADF',
    schedule=timedelta(hours=1),  # Run every 1 hour
    catchup=False,
    max_active_runs=1,
    tags=['nyc311', 'etl', 'azure', 'incremental']
)

# Define tasks
start = EmptyOperator(task_id='start', dag=dag)

extract = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    dag=dag
)

transform = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag
)

load_azure = PythonOperator(
    task_id='load_to_azure',
    python_callable=load_to_azure,
    dag=dag
)

trigger_adf = PythonOperator(
    task_id='trigger_adf_pipeline',
    python_callable=trigger_adf_pipeline,
    dag=dag
)

update_etl_state = PythonOperator(
    task_id='update_state',
    python_callable=update_state,
    dag=dag
)

cleanup = PythonOperator(
    task_id='cleanup_temp_files',
    python_callable=cleanup_temp_files,
    dag=dag,
    trigger_rule='all_done'  # Run even if previous tasks failed
)

end = EmptyOperator(task_id='end', dag=dag, trigger_rule='all_done')

# Define task dependencies
start >> extract >> transform >> load_azure >> trigger_adf >> update_etl_state >> cleanup >> end
