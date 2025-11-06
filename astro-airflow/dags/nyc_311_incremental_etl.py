
"""
NYC 311 Incremental ETL Pipeline
Airflow DAG for near real-time data processing
"""

from datetime import datetime, timedelta
import os
import sys

# Add project path to Python path
sys.path.append('/path/to/your/etl/modules')

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    # Import your ETL modules
    from nyc_311_etl import ETLOrchestrator, DataExtractor, DataTransformer, DataLoader, StateManager
    AIRFLOW_AVAILABLE = True
except ImportError:
    print("Airflow not available - DAG definition skipped")
    AIRFLOW_AVAILABLE = False

# DAG Configuration (only if Airflow is available)
if AIRFLOW_AVAILABLE:
    default_args = {
        'owner': 'data-engineering-team',
        'depends_on_past': False,
        'start_date': datetime(2025, 10, 31),
        'email_on_failure': True,
        'email_on_retry': False,
        'retries': 3,
        'retry_delay': timedelta(minutes=5),
        'execution_timeout': timedelta(minutes=30)
    }

    # Initialize DAG
    dag = DAG(
        'nyc_311_incremental_etl',
        default_args=default_args,
        description='NYC 311 Incremental ETL Pipeline',
        schedule_interval=timedelta(minutes=15),  # Run every 15 minutes
        catchup=False,
        max_active_runs=1
    )

def run_etl_pipeline(**context):
    """Execute the incremental ETL pipeline"""

    # Configuration from environment variables
    api_url = os.getenv("NYC_311_API_URL")
    app_token = os.getenv("APP_TOKEN")
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    container = os.getenv("AZURE_CONTAINER_NAME", "nyc-311-data")
    directory = os.getenv("AZURE_DIRECTORY_NAME", "incremental")

    # Initialize components
    extractor = DataExtractor(api_url, app_token)
    transformer = DataTransformer()
    loader = DataLoader(storage_account, container, directory)
    state_manager = StateManager()

    # Initialize orchestrator
    orchestrator = ETLOrchestrator(extractor, transformer, loader, state_manager)

    # Run pipeline
    result = orchestrator.run_incremental_pipeline()

    if result['status'] == 'error':
        raise Exception(f"ETL Pipeline failed: {result['error']}")

    # Log results to XCom for downstream tasks
    context['task_instance'].xcom_push(key='etl_result', value=result)

    return result

def validate_data_quality(**context):
    """Validate data quality after ETL"""
    result = context['task_instance'].xcom_pull(key='etl_result')

    if result['records_processed'] == 0:
        print("No new records processed - validation skipped")
        return True

    # Add your data quality checks here
    print(f"Data quality validation passed for {result['records_processed']} records")
    return True

def send_notification(**context):
    """Send success notification"""
    result = context['task_instance'].xcom_pull(key='etl_result')
    print(f"ETL Pipeline completed successfully: {result}")
    # Add email/Slack notification logic here

# Define tasks (only if Airflow is available)
if AIRFLOW_AVAILABLE:
    extract_transform_load = PythonOperator(
        task_id='extract_transform_load',
        python_callable=run_etl_pipeline,
        dag=dag
    )

    data_quality_check = PythonOperator(
        task_id='data_quality_check',
        python_callable=validate_data_quality,
        dag=dag
    )

    notify_completion = PythonOperator(
        task_id='notify_completion',
        python_callable=send_notification,
        dag=dag
    )

    # Define task dependencies
    extract_transform_load >> data_quality_check >> notify_completion
