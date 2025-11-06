"""
Transformation.py
Data transformation and cleaning module for NYC 311 service requests
Handles data quality, cleaning, and feature engineering
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataTransformer:
    """Handles data transformation and cleaning for NYC 311 data"""
    
    def __init__(self):
        """Initialize the data transformer"""
        self.borough_mapping = {
            'Queens': 'QUEENS',
            'Brooklyn': 'BROOKLYN', 
            'Manhattan': 'MANHATTAN',
            'Bronx': 'BRONX',
            'Staten Island': 'STATEN ISLAND',
            'Unspecified': 'UNSPECIFIED'
        }
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main transformation pipeline
        
        Args:
            df: Raw DataFrame to transform
            
        Returns:
            Cleaned and transformed DataFrame
        """
        if df.empty:
            logger.info("No data to transform")
            return df
        
        logger.info(f"Starting transformation of {len(df)} records")
        df_clean = df.copy()
        
        # Apply transformation steps
        df_clean = self._remove_duplicates(df_clean)
        df_clean = self._clean_coordinates(df_clean)
        df_clean = self._standardize_text_fields(df_clean)
        df_clean = self._standardize_boroughs(df_clean)
        df_clean = self._add_derived_columns(df_clean)
        df_clean = self._handle_missing_values(df_clean)
        df_clean = self._validate_data_quality(df_clean)
        df_clean = self._format_datetime_for_sql(df_clean)
        
        logger.info(f"Transformation completed: {len(df_clean)} records")
        return df_clean
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate records based on unique_key"""
        initial_count = len(df)
        df = df.drop_duplicates(subset=['unique_key'], keep='first')
        duplicates_removed = initial_count - len(df)
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate records")
        
        return df
    
    def _clean_coordinates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate latitude/longitude coordinates"""
        logger.info("Cleaning coordinate data")
        
        # Check if coordinate columns exist, if not create them with null values
        if 'latitude' not in df.columns:
            df['latitude'] = np.nan
        if 'longitude' not in df.columns:
            df['longitude'] = np.nan
        
        # Convert to numeric
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        
        # Validate NYC coordinates (approximate boundaries)
        valid_coords = (
            (df['latitude'].between(40.4, 41.0)) & 
            (df['longitude'].between(-74.5, -73.7))
        )
        
        # Set invalid coordinates to null
        invalid_mask = (~valid_coords) & df['latitude'].notna() & df['longitude'].notna()
        if invalid_mask.sum() > 0:
            logger.info(f"Found {invalid_mask.sum()} records with invalid coordinates - setting to null")
            df.loc[invalid_mask, ['latitude', 'longitude']] = np.nan
        
        return df
    
    def _standardize_text_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize text fields by cleaning and normalizing case"""
        logger.info("Standardizing text fields")
        
        text_fields = ['agency', 'complaint_type', 'descriptor', 'borough', 'status']
        
        for field in text_fields:
            if field in df.columns:
                # Clean and standardize
                df[field] = df[field].astype(str).str.strip().str.upper()
                # Replace 'NAN' string with actual NaN
                df[field] = df[field].replace('NAN', np.nan)
        
        return df
    
    def _standardize_boroughs(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize borough names to consistent format"""
        if 'borough' in df.columns:
            df['borough'] = df['borough'].map(
                lambda x: self.borough_mapping.get(x, x) if pd.notna(x) else x
            )
        
        return df
    
    def _add_derived_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived columns for analysis"""
        logger.info("Adding derived columns")
        
        # Date components
        if 'created_date' in df.columns:
            df['created_year'] = df['created_date'].dt.year
            df['created_month'] = df['created_date'].dt.month
            df['created_day'] = df['created_date'].dt.day
            df['created_hour'] = df['created_date'].dt.hour
            df['created_weekday'] = df['created_date'].dt.day_name()
        
        # Resolution time calculation
        if 'created_date' in df.columns and 'closed_date' in df.columns:
            df['resolution_hours'] = (
                df['closed_date'] - df['created_date']
            ).dt.total_seconds() / 3600
            
            # Remove negative resolution times (data quality issues)
            negative_mask = df['resolution_hours'] < 0
            if negative_mask.sum() > 0:
                logger.info(f"Found {negative_mask.sum()} records with negative resolution time")
                df.loc[negative_mask, 'resolution_hours'] = np.nan
        
        # Status flags
        if 'closed_date' not in df.columns:
            df['closed_date'] = np.nan
        df['is_closed'] = df['closed_date'].notna()
        df['has_location'] = df['latitude'].notna() & df['longitude'].notna()
        
        # Processing metadata
        df['processed_at'] = datetime.utcnow()
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values strategically"""
        logger.info("Handling missing values")
        
        # For categorical columns, create 'Unknown' category for NaN
        categorical_columns = ['agency', 'complaint_type', 'descriptor', 'borough', 'status']
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].fillna('UNKNOWN')
        
        return df
    
    def _validate_data_quality(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add data quality indicators"""
        logger.info("Calculating data quality metrics")
        
        # Calculate quality score (0-100)
        quality_score = 0
        quality_score += df['unique_key'].notna().astype(int) * 25  # Essential field
        quality_score += df['created_date'].notna().astype(int) * 20  # Important timestamp
        quality_score += df['has_location'].astype(int) * 20  # Location data
        quality_score += (df['complaint_type'] != 'UNKNOWN').astype(int) * 15  # Complaint type
        quality_score += (df['agency'] != 'UNKNOWN').astype(int) * 10  # Agency info
        quality_score += (df['borough'] != 'UNKNOWN').astype(int) * 10  # Borough info
        
        df['data_quality_score'] = quality_score
        
        # Remove completely empty rows
        empty_rows = df.isnull().all(axis=1)
        if empty_rows.sum() > 0:
            logger.info(f"Removing {empty_rows.sum()} completely empty rows")
            df = df[~empty_rows]
        
        return df
    
    def _format_datetime_for_sql(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format datetime columns for SQL Server compatibility"""
        logger.info("Formatting datetime columns for SQL Server")
        
        # List of datetime columns to format
        datetime_columns = ['created_date', 'closed_date', 'processed_at']
        
        for col in datetime_columns:
            if col in df.columns:
                # Convert pandas Timestamp to string in SQL Server-compatible format
                # Format: YYYY-MM-DD HH:MM:SS.fff
                df[col] = df[col].apply(
                    lambda x: x.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if pd.notna(x) else None
                )
        
        return df
    
    def get_transformation_summary(self, df_original: pd.DataFrame, df_transformed: pd.DataFrame) -> dict:
        """
        Generate transformation summary statistics
        
        Args:
            df_original: Original DataFrame before transformation
            df_transformed: Transformed DataFrame
            
        Returns:
            Dictionary with transformation statistics
        """
        return {
            'original_records': len(df_original),
            'transformed_records': len(df_transformed),
            'records_removed': len(df_original) - len(df_transformed),
            'columns_added': len(df_transformed.columns) - len(df_original.columns),
            'avg_quality_score': df_transformed['data_quality_score'].mean() if 'data_quality_score' in df_transformed.columns else 0,
            'records_with_location': df_transformed['has_location'].sum() if 'has_location' in df_transformed.columns else 0,
            'closed_complaints': df_transformed['is_closed'].sum() if 'is_closed' in df_transformed.columns else 0
        }


def main():
    """Main function for testing the transformer"""
    # Create sample data for testing
    sample_data = {
        'unique_key': ['1', '2', '2', '3'],  # Include duplicate
        'created_date': pd.to_datetime(['2025-10-31 10:00:00', '2025-10-31 11:00:00', 
                                       '2025-10-31 11:00:00', '2025-10-31 12:00:00']),
        'closed_date': pd.to_datetime(['2025-10-31 15:00:00', None, None, '2025-10-31 14:00:00']),
        'agency': ['NYPD', 'FDNY', 'FDNY', 'DOT'],
        'complaint_type': ['Noise', 'Fire', 'Fire', 'Pothole'],
        'borough': ['Manhattan', 'Brooklyn', 'Brooklyn', 'Queens'],
        'latitude': ['40.7589', '40.6892', '40.6892', '40.7282'],
        'longitude': ['-73.9851', '-73.9442', '-73.9442', '-73.7949']
    }
    
    df = pd.DataFrame(sample_data)
    
    # Initialize transformer
    transformer = DataTransformer()
    
    # Transform data
    df_transformed = transformer.transform(df)
    
    # Get summary
    summary = transformer.get_transformation_summary(df, df_transformed)
    
    print("Transformation Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print(f"\nTransformed columns: {list(df_transformed.columns)}")


if __name__ == "__main__":
    main()