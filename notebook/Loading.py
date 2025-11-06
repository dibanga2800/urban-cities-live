"""
Loading.py
Data loading module for NYC 311 service requests
Handles loading data to various destinations (Azure Data Lake, local storage)
"""

import os
import pandas as pd
import logging
from datetime import datetime
from typing import Optional
from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import DefaultAzureCredential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """Handles loading data to various storage destinations"""
    
    def __init__(self, 
                 storage_account: Optional[str] = None, 
                 container: Optional[str] = None, 
                 directory: Optional[str] = None):
        """
        Initialize the data loader
        
        Args:
            storage_account: Azure storage account name
            container: Azure container name
            directory: Directory within container
        """
        self.storage_account = storage_account or os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.container = container or os.getenv("AZURE_CONTAINER_NAME", "nyc-311-data")
        self.directory = directory or os.getenv("AZURE_DIRECTORY_NAME", "incremental")
        self.credential = DefaultAzureCredential()
    
    def load_to_azure_datalake(self, df: pd.DataFrame, file_prefix: str = "nyc_311") -> Optional[str]:
        """
        Load DataFrame to Azure Data Lake Storage
        
        Args:
            df: DataFrame to load
            file_prefix: Prefix for the filename
            
        Returns:
            Azure file path if successful, None if failed
        """
        if df.empty:
            logger.info("No data to load to Azure Data Lake")
            return None
        
        logger.info(f"Loading {len(df)} records to Azure Data Lake")
        
        try:
            # Initialize Azure Data Lake client
            service_client = DataLakeServiceClient(
                account_url=f"https://{self.storage_account}.dfs.core.windows.net",
                credential=self.credential
            )
            
            # Get file system client
            file_system_client = service_client.get_file_system_client(self.container)
            
            # Create container if it doesn't exist
            try:
                file_system_client.create_file_system()
                logger.info(f"Created container: {self.container}")
            except Exception:
                logger.debug(f"Container {self.container} already exists")
            
            # Generate file path with timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            file_path = f"{self.directory}/{file_prefix}_{timestamp}.csv"
            
            # Convert DataFrame to CSV
            csv_data = df.to_csv(index=False)
            
            # Upload file
            file_client = file_system_client.get_file_client(file_path)
            file_client.upload_data(csv_data, overwrite=True)
            
            logger.info(f"Successfully loaded to Azure Data Lake: {file_path}")
            logger.info(f"File size: {len(csv_data)} bytes, Records: {len(df)}")
            
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to load data to Azure Data Lake: {e}")
            raise
    
    def load_to_local(self, df: pd.DataFrame, 
                     file_prefix: str = "nyc_311", 
                     output_dir: str = "data/output") -> Optional[str]:
        """
        Load DataFrame to local storage as backup
        
        Args:
            df: DataFrame to load
            file_prefix: Prefix for the filename
            output_dir: Local output directory
            
        Returns:
            Local file path if successful
        """
        if df.empty:
            logger.info("No data to load locally")
            return None
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        local_path = os.path.join(output_dir, f"{file_prefix}_{timestamp}.csv")
        
        # Save to CSV
        df.to_csv(local_path, index=False)
        
        logger.info(f"Successfully saved locally: {local_path}")
        logger.info(f"Records: {len(df)}")
        
        return local_path
    
    def load_to_database(self, df: pd.DataFrame, 
                        table_name: str = "nyc_311_data", 
                        connection_string: Optional[str] = None) -> bool:
        """
        Load DataFrame to database (placeholder for future implementation)
        
        Args:
            df: DataFrame to load
            table_name: Target table name
            connection_string: Database connection string
            
        Returns:
            True if successful, False otherwise
        """
        if df.empty:
            logger.info("No data to load to database")
            return False
        
        # Placeholder for database implementation
        logger.info(f"Database loading not implemented yet for {len(df)} records")
        logger.info(f"Target table: {table_name}")
        
        # TODO: Implement database loading
        # - PostgreSQL using psycopg2
        # - SQL Server using pyodbc
        # - SQLite for testing
        
        return False
    
    def load_to_parquet(self, df: pd.DataFrame, 
                       file_prefix: str = "nyc_311", 
                       output_dir: str = "data/parquet") -> Optional[str]:
        """
        Load DataFrame to Parquet format for efficient storage
        
        Args:
            df: DataFrame to load
            file_prefix: Prefix for the filename
            output_dir: Output directory for Parquet files
            
        Returns:
            Parquet file path if successful
        """
        if df.empty:
            logger.info("No data to save as Parquet")
            return None
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        parquet_path = os.path.join(output_dir, f"{file_prefix}_{timestamp}.parquet")
        
        # Save to Parquet
        try:
            df.to_parquet(parquet_path, index=False, compression='snappy')
            logger.info(f"Successfully saved to Parquet: {parquet_path}")
            logger.info(f"Records: {len(df)}")
            return parquet_path
        except Exception as e:
            logger.error(f"Failed to save Parquet file: {e}")
            raise
    
    def load_multiple_formats(self, df: pd.DataFrame, 
                            file_prefix: str = "nyc_311",
                            save_local: bool = True,
                            save_azure: bool = True,
                            save_parquet: bool = True) -> dict:
        """
        Load DataFrame to multiple formats and destinations
        
        Args:
            df: DataFrame to load
            file_prefix: Prefix for filenames
            save_local: Whether to save locally
            save_azure: Whether to save to Azure
            save_parquet: Whether to save as Parquet
            
        Returns:
            Dictionary with file paths for each format
        """
        results = {}
        
        try:
            if save_local:
                results['local_csv'] = self.load_to_local(df, file_prefix)
            
            if save_parquet:
                results['local_parquet'] = self.load_to_parquet(df, file_prefix)
            
            if save_azure and self.storage_account:
                results['azure_path'] = self.load_to_azure_datalake(df, file_prefix)
            
            logger.info("Multi-format loading completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error in multi-format loading: {e}")
            raise
    
    def validate_azure_connection(self) -> bool:
        """
        Validate Azure Data Lake connection
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            if not self.storage_account:
                logger.error("Azure storage account not configured")
                return False
            
            service_client = DataLakeServiceClient(
                account_url=f"https://{self.storage_account}.dfs.core.windows.net",
                credential=self.credential
            )
            
            # Try to list file systems to test connection
            file_systems = list(service_client.list_file_systems())
            logger.info("Azure Data Lake connection validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Azure Data Lake connection failed: {e}")
            return False


class StateManager:
    """Manages ETL state for incremental loading"""
    
    def __init__(self, state_file: str = "data/etl_state.json"):
        """
        Initialize state manager
        
        Args:
            state_file: Path to state file
        """
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        """Load state from file"""
        if os.path.exists(self.state_file):
            try:
                import json
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load state file: {e}")
                return {}
        return {}
    
    def save_state(self, key: str, value) -> None:
        """Save state to file"""
        import json
        
        self.state[key] = value
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
    
    def get_last_processed_time(self) -> str:
        """Get last processed timestamp"""
        from datetime import timedelta
        # Default to October 29th, 2025 for initial data extraction
        default_time = datetime(2025, 10, 29, 0, 0, 0).isoformat()
        return self.state.get('last_processed_time', default_time)
    
    def update_last_processed_time(self, timestamp: str) -> None:
        """Update last processed timestamp"""
        self.save_state('last_processed_time', timestamp)


def main():
    """Main function for testing the loader"""
    # Create sample data for testing
    sample_data = {
        'unique_key': ['1', '2', '3'],
        'created_date': pd.to_datetime(['2025-10-31 10:00:00', '2025-10-31 11:00:00', '2025-10-31 12:00:00']),
        'complaint_type': ['Noise', 'Fire', 'Pothole'],
        'borough': ['MANHATTAN', 'BROOKLYN', 'QUEENS']
    }
    
    df = pd.DataFrame(sample_data)
    
    # Initialize loader
    loader = DataLoader()
    
    # Test local loading
    local_path = loader.load_to_local(df, "test_data")
    print(f"Local file saved: {local_path}")
    
    # Test Parquet loading
    parquet_path = loader.load_to_parquet(df, "test_data")
    print(f"Parquet file saved: {parquet_path}")
    
    # Test state manager
    state_mgr = StateManager()
    current_time = datetime.utcnow().isoformat()
    state_mgr.update_last_processed_time(current_time)
    print(f"Last processed time: {state_mgr.get_last_processed_time()}")


if __name__ == "__main__":
    main()