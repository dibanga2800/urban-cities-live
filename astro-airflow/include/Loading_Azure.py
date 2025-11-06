"""
Enhanced Loading.py
Data loading module with Azure Data Lake Gen2 and Azure Data Factory integration
Handles:
1. Loading raw data to ADLS raw container
2. Loading processed data to ADLS processed container  
3. Triggering ADF pipeline to copy processed data to SQL Database
"""

import os
import pandas as pd
import logging
from datetime import datetime
from typing import Optional, Dict
from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import *
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AzureDataLoader:
    """Enhanced data loader with ADLS Gen2 and Azure Data Factory integration"""
    
    def __init__(self):
        """Initialize Azure Data Loader with credentials from environment"""
        
        # Azure Storage Configuration
        self.storage_account = os.getenv("ADLS_ACCOUNT_NAME", "urbancitiesadls2025")
        self.storage_account_key = os.getenv("ADLS_ACCOUNT_KEY")
        
        # Container names
        self.raw_container = "raw"
        self.processed_container = "processed"
        self.curated_container = "curated"
        
        # Azure Data Factory Configuration
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID", "12f0f306-0cdf-41a6-9028-a7757690a1e2")
        self.resource_group = os.getenv("ADF_RESOURCE_GROUP", "urban-cities-rg")
        self.adf_name = os.getenv("ADF_NAME", "urban-cities-adf")
        
        # Azure credentials
        self.tenant_id = os.getenv("AZURE_TENANT_ID", "edc41ca9-a02a-4623-97cb-2a58f19e3c46")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        
        # Initialize credentials
        self._initialize_credentials()
        
        # Initialize Data Lake client
        self._initialize_datalake_client()
    
    def _initialize_credentials(self):
        """Initialize Azure credentials"""
        try:
            if self.client_id and self.client_secret:
                # Use Service Principal credentials
                self.credential = ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                logger.info("Using Service Principal authentication")
            else:
                # Use Azure CLI credentials (works with your existing login)
                from azure.identity import AzureCliCredential
                
                # Add Azure CLI to PATH for this process
                cli_path = r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"
                if os.path.exists(cli_path) and cli_path not in os.environ["PATH"]:
                    os.environ["PATH"] = cli_path + os.pathsep + os.environ["PATH"]
                    logger.info(f"Added Azure CLI to PATH: {cli_path}")
                
                try:
                    self.credential = AzureCliCredential()
                    # Test if it works by attempting to get a token
                    logger.info("✓ Using Azure CLI authentication (survives infrastructure changes)")
                except Exception as cli_error:
                    logger.warning(f"Azure CLI auth failed: {cli_error}")
                    logger.info("Falling back to DefaultAzureCredential")
                    self.credential = DefaultAzureCredential()
        except Exception as e:
            logger.error(f"Error initializing credentials: {e}")
            raise
    
    def _initialize_datalake_client(self):
        """Initialize Data Lake Service Client using best available authentication method"""
        try:
            account_url = f"https://{self.storage_account}.dfs.core.windows.net"
            
            # Prefer Azure AD credential authentication (survives infrastructure changes!)
            # Only use storage key as fallback for compatibility
            if self.storage_account_key:
                logger.warning("⚠ Using storage account key (will break on infrastructure rebuild)")
                self.datalake_client = DataLakeServiceClient(
                    account_url=account_url,
                    credential=self.storage_account_key
                )
                logger.info("✓ Storage account key authentication active")
            else:
                # Azure AD credential authentication - RECOMMENDED
                # Survives infrastructure destroy/recreate cycles
                self.datalake_client = DataLakeServiceClient(
                    account_url=account_url,
                    credential=self.credential
                )
                logger.info("✓ Azure AD credential authentication active (infrastructure-independent)")
                
        except Exception as e:
            logger.error(f"Error initializing Data Lake client: {e}")
            raise
    
    def load_to_raw_container(self, df: pd.DataFrame, file_prefix: str = "nyc_311") -> Optional[str]:
        """
        Load raw extracted data to ADLS raw container
        
        Args:
            df: DataFrame containing raw data
            file_prefix: Prefix for the filename
            
        Returns:
            File path if successful, None if failed
        """
        if df.empty:
            logger.warning("Empty DataFrame - nothing to load to raw container")
            return None
        
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{file_prefix}_raw_{timestamp}.csv"
            file_path = f"raw-data/{filename}"
            
            # Get file system client
            file_system_client = self.datalake_client.get_file_system_client(self.raw_container)
            
            # Create directory if it doesn't exist
            try:
                directory_client = file_system_client.get_directory_client("raw-data")
                directory_client.create_directory()
            except Exception:
                pass  # Directory may already exist
            
            # Upload file
            file_client = file_system_client.get_file_client(file_path)
            
            # Convert DataFrame to CSV
            csv_data = df.to_csv(index=False)
            
            # Upload data
            file_client.upload_data(csv_data, overwrite=True)
            
            logger.info(f"Successfully uploaded {len(df)} records to raw container: {file_path}")
            logger.info(f"File size: {len(csv_data)} bytes")
            
            return f"abfss://{self.raw_container}@{self.storage_account}.dfs.core.windows.net/{file_path}"
            
        except Exception as e:
            logger.error(f"Error loading data to raw container: {e}")
            return None
    
    def load_to_processed_container(self, df: pd.DataFrame, file_prefix: str = "nyc_311") -> Optional[str]:
        """
        Load transformed/processed data to ADLS processed container
        Uses Parquet format for efficient storage and better compression
        
        Args:
            df: DataFrame containing processed data
            file_prefix: Prefix for the filename
            
        Returns:
            File path if successful, None if failed
        """
        if df.empty:
            logger.warning("Empty DataFrame - nothing to load to processed container")
            return None
        
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{file_prefix}_processed_{timestamp}.parquet"
            file_path = f"processed-data/{filename}"
            
            # Get file system client
            file_system_client = self.datalake_client.get_file_system_client(self.processed_container)
            
            # Create directory if it doesn't exist
            try:
                directory_client = file_system_client.get_directory_client("processed-data")
                directory_client.create_directory()
            except Exception:
                pass  # Directory may already exist
            
            # Upload file
            file_client = file_system_client.get_file_client(file_path)
            
            # Convert DataFrame to Parquet format (in-memory)
            import io
            import pyarrow as pa
            import pyarrow.parquet as pq
            
            buffer = io.BytesIO()
            
            # Ensure datetime-like columns are proper timestamps in Parquet (for ADF to map to SQL DateTime)
            datetime_cols = ['created_date', 'closed_date', 'processed_at']
            for col in datetime_cols:
                if col in df.columns:
                    # Normalize known null tokens then convert
                    df[col] = df[col].replace({'': None, 'NaT': None, 'None': None})
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            # Create PyArrow table letting Arrow infer proper types (timestamps, numerics, strings)
            table = pa.Table.from_pandas(df, preserve_index=False)
            
            # Log for debugging
            for col in datetime_cols:
                if col in df.columns:
                    try:
                        logger.info(f"{col} - Parquet type: {table.schema.field(col).type}, nulls: {table.column(col).null_count}")
                    except Exception:
                        pass
            
            # Write to Parquet, coercing timestamps to milliseconds so ADF interprets as DateTime
            pq.write_table(
                table,
                buffer,
                coerce_timestamps='ms',
                allow_truncated_timestamps=True
            )
            parquet_data = buffer.getvalue()
            
            # Upload data
            file_client.upload_data(parquet_data, overwrite=True)
            
            logger.info(f"Successfully uploaded {len(df)} records to processed container: {file_path}")
            logger.info(f"File size: {len(parquet_data)} bytes (Parquet format)")
            
            return f"abfss://{self.processed_container}@{self.storage_account}.dfs.core.windows.net/{file_path}"
            
        except Exception as e:
            logger.error(f"Error loading data to processed container: {e}")
            return None
    
    def trigger_adf_pipeline(self, 
                            pipeline_name: str = "CopyProcessedDataToSQL",
                            source_file_path: Optional[str] = None,
                            parameters: Optional[Dict] = None) -> Dict:
        """
        Trigger Azure Data Factory pipeline to copy processed data to SQL Database
        
        Args:
            pipeline_name: Name of the ADF pipeline to trigger
            source_file_path: Path to the source file in ADLS
            parameters: Additional parameters to pass to the pipeline
            
        Returns:
            Dict with run_id and status
        """
        try:
            # Helper to extract just the file name relative to processed-data folder
            def _to_file_name(path: str) -> str:
                if not path:
                    return path
                # Strip abfss URL and directory prefixes
                for token in ["abfss://", f"{self.processed_container}@{self.storage_account}.dfs.core.windows.net/", f"{self.storage_account}.dfs.core.windows.net/", "https://", "http://"]:
                    path = path.replace(token, "")
                # Remove container and folder prefixes if present
                path = path.replace(f"{self.processed_container}/", "")
                path = path.replace("processed-data/", "")
                return os.path.basename(path)

            # Initialize ADF Management Client
            adf_client = DataFactoryManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )
            
            # Prepare pipeline parameters
            pipeline_params = parameters or {}
            
            # Determine target file name: prefer explicit, else discover latest
            file_name = None
            if source_file_path:
                file_name = _to_file_name(source_file_path)
            if not file_name:
                try:
                    # Discover latest parquet in processed-data
                    fs = self.datalake_client.get_file_system_client(self.processed_container)
                    paths = list(fs.get_paths(path="processed-data"))
                    parquet_files = [p for p in paths if (not p.is_directory and p.name.endswith('.parquet'))]
                    parquet_files.sort(key=lambda p: p.last_modified, reverse=True)
                    if parquet_files:
                        file_name = os.path.basename(parquet_files[0].name)
                        logger.info(f"Discovered latest Parquet: {file_name}")
                except Exception as disc_err:
                    logger.warning(f"Could not discover latest Parquet automatically: {disc_err}")

            if file_name:
                pipeline_params['fileName'] = file_name
            else:
                logger.warning("No Parquet file name provided or discovered; pipeline may not copy any file.")
            
            pipeline_params['timestamp'] = datetime.now().isoformat()
            
            logger.info(f"Triggering ADF pipeline: {pipeline_name}")
            logger.info(f"Parameters: {pipeline_params}")
            
            # Create pipeline run
            run_response = adf_client.pipelines.create_run(
                resource_group_name=self.resource_group,
                factory_name=self.adf_name,
                pipeline_name=pipeline_name,
                parameters=pipeline_params
            )
            
            run_id = run_response.run_id
            logger.info(f"Pipeline run created with ID: {run_id}")
            
            # Wait for pipeline to complete (with timeout)
            timeout = 600  # 10 minutes timeout
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                pipeline_run = adf_client.pipeline_runs.get(
                    resource_group_name=self.resource_group,
                    factory_name=self.adf_name,
                    run_id=run_id
                )
                
                status = pipeline_run.status
                logger.info(f"Pipeline status: {status}")
                
                if status in ['Succeeded', 'Failed', 'Cancelled']:
                    break
                
                time.sleep(10)  # Check every 10 seconds
            
            # Get final status
            final_run = adf_client.pipeline_runs.get(
                resource_group_name=self.resource_group,
                factory_name=self.adf_name,
                run_id=run_id
            )
            
            result = {
                'run_id': run_id,
                'status': final_run.status,
                'message': final_run.message if hasattr(final_run, 'message') else None,
                'duration_ms': final_run.duration_in_ms if hasattr(final_run, 'duration_in_ms') else None
            }
            
            if final_run.status == 'Succeeded':
                logger.info(f"ADF pipeline completed successfully: {run_id}")
            else:
                logger.error(f"ADF pipeline failed with status: {final_run.status}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error triggering ADF pipeline: {e}")
            return {
                'run_id': None,
                'status': 'Error',
                'message': str(e)
            }
    
    def load_complete_pipeline(self, 
                               raw_df: pd.DataFrame, 
                               processed_df: pd.DataFrame,
                               trigger_adf: bool = True) -> Dict:
        """
        Complete loading pipeline: raw -> ADLS, processed -> ADLS, trigger ADF
        
        Args:
            raw_df: Raw extracted DataFrame
            processed_df: Processed/transformed DataFrame
            trigger_adf: Whether to trigger ADF pipeline to load to SQL
            
        Returns:
            Dict with results of all operations
        """
        results = {
            'raw_upload': None,
            'processed_upload': None,
            'adf_run': None,
            'status': 'pending'
        }
        
        try:
            # Step 1: Load raw data to ADLS raw container
            logger.info("Step 1: Loading raw data to ADLS...")
            raw_path = self.load_to_raw_container(raw_df)
            results['raw_upload'] = {
                'path': raw_path,
                'records': len(raw_df),
                'status': 'success' if raw_path else 'failed'
            }
            
            # Step 2: Load processed data to ADLS processed container
            logger.info("Step 2: Loading processed data to ADLS...")
            processed_path = self.load_to_processed_container(processed_df)
            results['processed_upload'] = {
                'path': processed_path,
                'records': len(processed_df),
                'status': 'success' if processed_path else 'failed'
            }
            
            # Step 3: Trigger ADF pipeline to load processed data to SQL
            if trigger_adf and processed_path:
                logger.info("Step 3: Triggering ADF pipeline to load to SQL Database...")
                adf_result = self.trigger_adf_pipeline(
                    pipeline_name="CopyProcessedToSQL",
                    source_file_path=processed_path
                )
                results['adf_run'] = adf_result
            
            # Determine overall status
            if (results['raw_upload']['status'] == 'success' and 
                results['processed_upload']['status'] == 'success'):
                if trigger_adf:
                    results['status'] = 'success' if results['adf_run']['status'] == 'Succeeded' else 'partial'
                else:
                    results['status'] = 'success'
            else:
                results['status'] = 'failed'
            
            logger.info(f"Complete pipeline finished with status: {results['status']}")
            return results
            
        except Exception as e:
            logger.error(f"Error in complete loading pipeline: {e}")
            results['status'] = 'error'
            results['error'] = str(e)
            return results


# Backward compatibility - keep old class name as alias
DataLoader = AzureDataLoader


if __name__ == "__main__":
    # Test the loader
    from dotenv import load_dotenv
    load_dotenv()
    
    loader = AzureDataLoader()
    
    # Test with sample data
    test_df = pd.DataFrame({
        'unique_key': [1, 2, 3],
        'created_date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'complaint_type': ['Noise', 'Heating', 'Water']
    })
    
    # Test raw upload
    print("Testing raw data upload...")
    raw_path = loader.load_to_raw_container(test_df, "test")
    print(f"Raw upload result: {raw_path}")
    
    # Test processed upload
    print("\nTesting processed data upload...")
    processed_path = loader.load_to_processed_container(test_df, "test")
    print(f"Processed upload result: {processed_path}")
    
    # Test complete pipeline
    print("\nTesting complete pipeline...")
    results = loader.load_complete_pipeline(test_df, test_df, trigger_adf=False)
    print(f"Complete pipeline results: {results}")
