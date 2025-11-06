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

# Add project path to Python path
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_path)

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.operators.dummy import DummyOperator
    from airflow.utils.dates import days_ago
    AIRFLOW_AVAILABLE = True
except ImportError:
    print("Airflow not available - DAG definition skipped")
    AIRFLOW_AVAILABLE = False

# Import ETL modules
try:
    from Extraction import DataExtractor
    from Transformation import DataTransformer
    from Loading_Azure import AzureDataLoader
    import json
except ImportError as e:
    print(f"Error importing ETL modules: {e}")
    DataExtractor = None
    DataTransformer = None
    AzureDataLoader = None

# State file for tracking last processed timestamp
STATE_FILE = os.path.join(project_path, 'data', 'etl_state.json')

def load_state():
    """Load last processed timestamp from state file"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                return state.get('last_processed_time')
    except Exception as e:
        print(f"Error loading state: {e}")
    
    # Default to 24 hours ago if no state exists
    return (datetime.now() - timedelta(hours=24)).isoformat()

def save_state(timestamp):
    """Save last processed timestamp to state file"""
    try:
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
    output_dir = os.path.join(project_path, 'data', 'temp')
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
    
    # Calculate data quality metrics
    quality_metrics = transformer.calculate_quality_metrics(df, transformed_df)
    print(f"Data quality metrics: {quality_metrics}")
    
    # Save to XCom
    context['task_instance'].xcom_push(key='processed_data_count', value=len(transformed_df))
    context['task_instance'].xcom_push(key='quality_metrics', value=quality_metrics)
    
    # Save processed data to temporary file
    output_dir = os.path.dirname(raw_file)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    processed_file = os.path.join(output_dir, f'processed_{timestamp}.csv')
    transformed_df.to_csv(processed_file, index=False)
    
    context['task_instance'].xcom_push(key='processed_file_path', value=processed_file)
    
    print(f"Processed data saved to: {processed_file}")
    print("=" * 50)
    
    return len(transformed_df)

def load_to_azure(**context):
    """Load data to Azure Data Lake Storage"""
    print("=" * 50)
    print("STEP 3: LOADING DATA TO AZURE DATA LAKE")
    print("=" * 50)
    
    # Get file paths
    raw_file = context['task_instance'].xcom_pull(key='raw_file_path', task_ids='extract_data')
    processed_file = context['task_instance'].xcom_pull(key='processed_file_path', task_ids='transform_data')
    
    if not raw_file or not processed_file:
        print("No data files found - skipping load")
        return {'status': 'skipped'}
    
    # Load data
    raw_df = pd.read_csv(raw_file)
    processed_df = pd.read_csv(processed_file)
    
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
    """Trigger Azure Data Factory pipeline to copy data to SQL Database"""
    print("=" * 50)
    print("STEP 4: TRIGGERING AZURE DATA FACTORY PIPELINE")
    print("=" * 50)
    
    # Get processed file path from ADLS
    processed_path = context['task_instance'].xcom_pull(key='processed_adls_path', task_ids='load_to_azure')
    
    if not processed_path:
        print("No processed data path found - skipping ADF trigger")
        return {'status': 'skipped'}
    
    print(f"Triggering ADF to copy data from: {processed_path}")
    
    # Initialize Azure loader (for ADF client)
    loader = AzureDataLoader()
    
    # Trigger ADF pipeline
    adf_result = loader.trigger_adf_pipeline(
        pipeline_name="CopyProcessedDataToSQL",
        source_file_path=processed_path
    )
    
    print(f"\nADF Pipeline Result:")
    print(f"  Run ID: {adf_result.get('run_id')}")
    print(f"  Status: {adf_result.get('status')}")
    print(f"  Duration: {adf_result.get('duration_ms')} ms")
    
    context['task_instance'].xcom_push(key='adf_run_id', value=adf_result.get('run_id'))
    context['task_instance'].xcom_push(key='adf_status', value=adf_result.get('status'))
    
    print("=" * 50)
    
    return adf_result

def update_state(**context):
    """Update ETL state with latest processed timestamp"""
    print("=" * 50)
    print("STEP 5: UPDATING ETL STATE")
    print("=" * 50)
    
    # Get processed file to extract max timestamp
    processed_file = context['task_instance'].xcom_pull(key='processed_file_path', task_ids='transform_data')
    
    if processed_file and os.path.exists(processed_file):
        df = pd.read_csv(processed_file)
        if len(df) > 0 and 'created_date' in df.columns:
            latest_timestamp = df['created_date'].max()
            save_state(latest_timestamp)
            print(f"State updated with timestamp: {latest_timestamp}")
        else:
            print("No data to update state")
    else:
        print("No processed data found - state not updated")
    
    print("=" * 50)

def cleanup_temp_files(**context):
    """Clean up temporary files"""
    print("Cleaning up temporary files...")
    
    raw_file = context['task_instance'].xcom_pull(key='raw_file_path', task_ids='extract_data')
    processed_file = context['task_instance'].xcom_pull(key='processed_file_path', task_ids='transform_data')
    
    for file_path in [raw_file, processed_file]:
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

# Define DAG (only if Airflow is available)
if AIRFLOW_AVAILABLE:
    default_args = {
        'owner': 'data-engineering-team',
        'depends_on_past': False,
        'start_date': days_ago(1),
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
        schedule_interval=timedelta(minutes=15),  # Run every 15 minutes
        catchup=False,
        max_active_runs=1,
        tags=['nyc311', 'etl', 'azure', 'incremental']
    )

    # Define tasks
    start = DummyOperator(task_id='start', dag=dag)
    
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
    
    notify = PythonOperator(
        task_id='send_notification',
        python_callable=send_notification,
        dag=dag,
        trigger_rule='all_done'
    )
    
    end = DummyOperator(task_id='end', dag=dag, trigger_rule='all_done')

    # Define task dependencies
    start >> extract >> transform >> load_azure >> trigger_adf >> update_etl_state >> cleanup >> notify >> end

    print("DAG 'nyc_311_incremental_etl_azure' created successfully")
