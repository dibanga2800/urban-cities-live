"""
dag_script.py
Apache Airflow DAG for NYC 311 Incremental ETL Pipeline
Orchestrates the complete ETL workflow with scheduling and monitoring
"""

from datetime import datetime, timedelta
import os
import sys
import logging
import pandas as pd

# Add current directory to Python path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import Airflow (graceful handling if not installed)
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.operators.email import EmailOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    logger.warning("Airflow not available - DAG definition will be skipped")
    AIRFLOW_AVAILABLE = False

# Import our ETL modules
try:
    from Extraction import DataExtractor
    from Transformation import DataTransformer
    from Loading import DataLoader, StateManager
    ETL_MODULES_AVAILABLE = True
except ImportError as e:
    logger.error(f"ETL modules not available: {e}")
    ETL_MODULES_AVAILABLE = False


class ETLOrchestrator:
    """Main ETL pipeline orchestrator"""
    
    def __init__(self):
        """Initialize the ETL orchestrator with configuration"""
        self.config = self._load_config()
        self.extractor = DataExtractor(
            api_url=self.config['api_url'],
            app_token=self.config['app_token'],
            batch_size=self.config['batch_size']
        )
        self.transformer = DataTransformer()
        self.loader = DataLoader(
            storage_account=self.config['storage_account'],
            container=self.config['container'],
            directory=self.config['directory']
        )
        self.state_manager = StateManager(self.config['state_file'])
    
    def _load_config(self) -> dict:
        """Load configuration from environment variables"""
        return {
            'api_url': os.getenv("NYC_311_API_URL", "https://data.cityofnewyork.us/resource/erm2-nwe9.json"),
            'app_token': os.getenv("APP_TOKEN"),
            'batch_size': int(os.getenv("BATCH_SIZE", "1000")),
            'storage_account': os.getenv("AZURE_STORAGE_ACCOUNT_NAME"),
            'container': os.getenv("AZURE_CONTAINER_NAME", "nyc-311-data"),
            'directory': os.getenv("AZURE_DIRECTORY_NAME", "incremental"),
            'state_file': os.getenv("STATE_FILE", "data/etl_state.json")
        }
    
    def run_incremental_pipeline(self) -> dict:
        """
        Run the complete incremental ETL pipeline
        
        Returns:
            Dictionary with pipeline execution results
        """
        try:
            logger.info("Starting incremental ETL pipeline")
            
            # 1. Extract incremental data
            last_processed = self.state_manager.get_last_processed_time()
            logger.info(f"Extracting data since: {last_processed}")
            
            df_raw = self.extractor.extract_incremental(last_processed)
            
            if df_raw.empty:
                logger.info("No new data found - pipeline completed")
                return {
                    "status": "success",
                    "records_processed": 0,
                    "message": "No new data to process"
                }
            
            # 2. Transform data
            logger.info(f"Transforming {len(df_raw)} records")
            df_original = df_raw.copy()
            df_transformed = self.transformer.transform(df_raw)
            
            # 3. Load data to multiple destinations
            logger.info("Loading data to destinations")
            load_results = self.loader.load_multiple_formats(
                df_transformed, 
                file_prefix="nyc_311_incremental"
            )
            
            # 4. Update processing state
            if 'created_date' in df_transformed.columns:
                max_created_date = df_transformed['created_date'].max()
                if pd.notna(max_created_date):
                    self.state_manager.update_last_processed_time(max_created_date.isoformat())
            
            # 5. Generate summary
            transformation_summary = self.transformer.get_transformation_summary(
                df_original, df_transformed
            )
            
            result = {
                "status": "success",
                "records_processed": len(df_transformed),
                "transformation_summary": transformation_summary,
                "load_results": load_results,
                "execution_time": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Pipeline completed successfully: {result}")
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "execution_time": datetime.utcnow().isoformat()
            }
            logger.error(f"Pipeline failed: {error_result}")
            return error_result


# Airflow DAG Definition (only if Airflow is available)
if AIRFLOW_AVAILABLE and ETL_MODULES_AVAILABLE:
    
    # DAG Configuration
    default_args = {
        'owner': 'data-engineering-team',
        'depends_on_past': False,
        'start_date': datetime(2025, 10, 29),
        'email_on_failure': True,
        'email_on_retry': False,
        'retries': 3,
        'retry_delay': timedelta(minutes=5),
        'execution_timeout': timedelta(minutes=30),
        'email': ['data-team@company.com']  # Configure your email
    }
    
    # Initialize DAG
    dag = DAG(
        'nyc_311_incremental_etl',
        default_args=default_args,
        description='NYC 311 Incremental ETL Pipeline - Production',
        schedule=timedelta(minutes=15),  # Run every 15 minutes
        catchup=False,
        max_active_runs=1,
        tags=['nyc311', 'etl', 'incremental', 'production']
    )
    
    def run_etl_pipeline(**context):
        """Airflow task to execute the incremental ETL pipeline"""
        orchestrator = ETLOrchestrator()
        result = orchestrator.run_incremental_pipeline()
        
        # Push results to XCom for downstream tasks
        context['task_instance'].xcom_push(key='etl_result', value=result)
        
        if result['status'] == 'error':
            raise Exception(f"ETL Pipeline failed: {result['error']}")
        
        return result
    
    def validate_data_quality(**context):
        """Airflow task to validate data quality after ETL"""
        result = context['task_instance'].xcom_pull(key='etl_result')
        
        if result['records_processed'] == 0:
            logger.info("No new records processed - data quality validation skipped")
            return True
        
        # Data quality checks
        transformation_summary = result.get('transformation_summary', {})
        avg_quality_score = transformation_summary.get('avg_quality_score', 0)
        
        # Quality thresholds
        min_quality_score = 80
        
        if avg_quality_score < min_quality_score:
            raise Exception(f"Data quality below threshold: {avg_quality_score} < {min_quality_score}")
        
        logger.info(f"Data quality validation passed: avg score = {avg_quality_score}")
        return True
    
    def send_success_notification(**context):
        """Airflow task to send success notification"""
        result = context['task_instance'].xcom_pull(key='etl_result')
        
        message = f"""
        NYC 311 ETL Pipeline Completed Successfully
        
        Execution Time: {result.get('execution_time')}
        Records Processed: {result.get('records_processed', 0)}
        
        Transformation Summary:
        {result.get('transformation_summary', {})}
        
        Load Results:
        {result.get('load_results', {})}
        """
        
        logger.info(f"Pipeline success notification: {message}")
        return message
    
    def handle_failure_notification(context):
        """Callback function for handling task failures"""
        task_instance = context['task_instance']
        dag_run = context['dag_run']
        
        error_message = f"""
        NYC 311 ETL Pipeline Failed
        
        DAG: {dag_run.dag_id}
        Task: {task_instance.task_id}
        Execution Date: {dag_run.execution_date}
        Log URL: {task_instance.log_url}
        """
        
        logger.error(f"Pipeline failure notification: {error_message}")
        # Here you could send to Slack, email, or other notification systems
        return error_message
    
    # Define Airflow tasks
    extract_transform_load = PythonOperator(
        task_id='extract_transform_load',
        python_callable=run_etl_pipeline,
        dag=dag,
        on_failure_callback=handle_failure_notification
    )
    
    data_quality_check = PythonOperator(
        task_id='data_quality_check',
        python_callable=validate_data_quality,
        dag=dag,
        on_failure_callback=handle_failure_notification
    )
    
    success_notification = PythonOperator(
        task_id='success_notification',
        python_callable=send_success_notification,
        dag=dag
    )
    
    # Define task dependencies
    extract_transform_load >> data_quality_check >> success_notification

else:
    logger.info("DAG not created - missing dependencies")


def main():
    """Main function for testing the ETL orchestrator"""
    if not ETL_MODULES_AVAILABLE:
        print("ETL modules not available - cannot run test")
        return
    
    # Test the orchestrator
    orchestrator = ETLOrchestrator()
    result = orchestrator.run_incremental_pipeline()
    
    print("\n" + "="*50)
    print("ETL PIPELINE TEST RESULTS")
    print("="*50)
    print(f"Status: {result['status']}")
    print(f"Records Processed: {result.get('records_processed', 0)}")
    
    if result['status'] == 'success' and result['records_processed'] > 0:
        print(f"Transformation Summary: {result.get('transformation_summary', {})}")
        print(f"Load Results: {result.get('load_results', {})}")
    elif result['status'] == 'error':
        print(f"Error: {result.get('error')}")
    
    print("="*50)


if __name__ == "__main__":
    main()