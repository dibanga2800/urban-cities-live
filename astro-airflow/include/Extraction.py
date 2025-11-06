"""
Extraction.py
Data extraction module for NYC 311 service requests
Handles incremental data fetching from the NYC 311 API
"""

import os
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataExtractor:
    """Handles incremental data extraction from NYC 311 API"""
    
    def __init__(self, api_url: str, app_token: Optional[str] = None, batch_size: int = 1000):
        """
        Initialize the data extractor
        
        Args:
            api_url: NYC 311 API endpoint URL
            app_token: Optional API token for authentication
            batch_size: Number of records to fetch per batch
        """
        self.api_url = api_url
        self.app_token = app_token
        self.batch_size = batch_size
        self.headers = {"X-App-Token": app_token} if app_token else {}
    
    def extract_incremental(self, since_time: str) -> pd.DataFrame:
        """
        Extract data incrementally since given timestamp
        
        Args:
            since_time: ISO timestamp string to fetch data from
            
        Returns:
            DataFrame containing extracted records
        """
        # Convert timestamp to proper format for Socrata API
        # Socrata expects ISO 8601 format: YYYY-MM-DDTHH:MM:SS
        try:
            # Parse the input timestamp and format it correctly
            if '.' in since_time:
                # Remove milliseconds if present
                since_time = since_time.split('.')[0]
            # Ensure T separator between date and time
            if ' ' in since_time:
                since_time = since_time.replace(' ', 'T')
        except Exception as e:
            logger.warning(f"Could not reformat timestamp: {e}, using as-is")
        
        logger.info(f"Extracting data since: {since_time}")
        
        all_records = []
        offset = 0
        
        while True:
            params = {
                "$limit": self.batch_size,
                "$offset": offset,
                "$where": f"created_date >= '{since_time}'",
                "$order": "created_date ASC"
            }
            
            try:
                response = requests.get(
                    self.api_url, 
                    params=params, 
                    headers=self.headers, 
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    break
                
                all_records.extend(data)
                offset += self.batch_size
                logger.info(f"Fetched {len(data)} records (Total: {len(all_records)})")
                
            except requests.RequestException as e:
                logger.error(f"API request failed: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during extraction: {e}")
                raise
        
        # Convert to DataFrame
        if all_records:
            df = self._process_raw_data(all_records)
            logger.info(f"Successfully extracted {len(df)} records")
            return df
        
        logger.info("No new records found")
        return pd.DataFrame()
    
    def _process_raw_data(self, records: list) -> pd.DataFrame:
        """
        Process raw API data into structured DataFrame
        
        Args:
            records: List of raw API response records
            
        Returns:
            Processed DataFrame
        """
        df = pd.DataFrame(records)
        
        # Select standard columns
        required_columns = [
            "unique_key", "created_date", "closed_date", "agency", 
            "complaint_type", "descriptor", "borough", "status", 
            "latitude", "longitude"
        ]
        
        available_columns = [col for col in required_columns if col in df.columns]
        df = df[available_columns]
        
        # Parse dates
        for date_col in ["created_date", "closed_date"]:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        
        return df
    
    def extract_full_data(self, days_back: int = 7) -> pd.DataFrame:
        """
        Extract full data for the specified number of days back
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            DataFrame containing extracted records
        """
        since_time = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%S")
        return self.extract_incremental(since_time)


def main():
    """Main function for testing the extractor"""
    # Configuration from environment variables
    API_URL = os.getenv("NYC_311_API_URL", "https://data.cityofnewyork.us/resource/erm2-nwe9.json")
    APP_TOKEN = os.getenv("APP_TOKEN")
    
    # Initialize extractor
    extractor = DataExtractor(API_URL, APP_TOKEN)
    
    # Test extraction
    test_time = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
    df = extractor.extract_incremental(test_time)
    
    print(f"Extracted {len(df)} records")
    if not df.empty:
        print(f"Columns: {list(df.columns)}")
        print(f"Date range: {df['created_date'].min()} to {df['created_date'].max()}")


if __name__ == "__main__":
    main()