"""
Complete ETL Pipeline Test with Azure Integration
Tests: Extract → Transform → Load to ADLS (raw + processed)
"""

import os
import sys
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our ETL modules
from Extraction import DataExtractor
from Transformation import DataTransformer
from Loading_Azure import AzureDataLoader

def test_complete_etl_pipeline():
    """Test the complete ETL pipeline with Azure integration"""
    
    print("\n" + "="*60)
    print("  NYC 311 ETL PIPELINE TEST - AZURE INTEGRATION")
    print("="*60 + "\n")
    
    try:
        # Step 1: Initialize components
        print("Step 1: Initializing ETL components...")
        
        # Extractor
        api_url = os.getenv("NYC_311_API_URL", "https://data.cityofnewyork.us/resource/erm2-nwe9.json")
        app_token = os.getenv("NYC_APP_TOKEN")
        
        extractor = DataExtractor(
            api_url=api_url,
            app_token=app_token,
            batch_size=100  # Small batch for testing
        )
        print(f"   ✓ Extractor initialized (API: {api_url})")
        
        # Transformer
        transformer = DataTransformer()
        print("   ✓ Transformer initialized")
        
        # Azure Loader
        loader = AzureDataLoader()
        print(f"   ✓ Azure Loader initialized")
        print(f"     - Storage: {loader.storage_account}")
        print(f"     - Containers: {loader.raw_container}, {loader.processed_container}")
        print()
        
        # Step 2: Extract data
        print("Step 2: Extracting data from NYC 311 API...")
        
        # Get most recent records (last 24 hours)
        from datetime import timedelta
        last_24h = (datetime.now() - timedelta(days=1)).isoformat()
        
        df_raw = extractor.extract_incremental(since_time=last_24h)
        
        if df_raw.empty:
            print("   ⚠ No new data found in last 24 hours")
            print("   Testing with sample data instead...")
            
            # Create sample data for testing
            now = datetime.now()
            df_raw = pd.DataFrame({
                'unique_key': ['12345', '12346', '12347'],
                'created_date': pd.to_datetime([now.isoformat()] * 3),
                'agency': ['NYPD', 'DOT', 'DSNY'],
                'complaint_type': ['Noise', 'Street Condition', 'Sanitation'],
                'descriptor': ['Loud Music', 'Pothole', 'Dirty Conditions'],
                'location_type': ['Street/Sidewalk', 'Street', 'Street'],
                'incident_zip': ['10001', '10002', '10003'],
                'city': ['NEW YORK', 'NEW YORK', 'NEW YORK'],
                'status': ['Open', 'Assigned', 'Closed'],
                'borough': ['MANHATTAN', 'MANHATTAN', 'BROOKLYN'],
                'latitude': [40.750, 40.751, 40.652],
                'longitude': [-73.997, -73.998, -73.950]
            })
        
        print(f"   ✓ Extracted {len(df_raw)} records")
        print(f"     - Columns: {len(df_raw.columns)}")
        print(f"     - Sample columns: {', '.join(df_raw.columns[:5].tolist())}")
        print()
        
        # Step 3: Transform data
        print("Step 3: Transforming data...")
        
        df_original = df_raw.copy()
        df_transformed = transformer.transform(df_raw)
        
        # Get transformation summary
        summary = transformer.get_transformation_summary(df_original, df_transformed)
        
        print(f"   ✓ Transformed {len(df_transformed)} records")
        print(f"     - Original records: {summary['original_records']}")
        print(f"     - Transformed records: {summary['transformed_records']}")
        print(f"     - Columns added: {summary['columns_added']}")
        print(f"     - Quality score: {summary['avg_quality_score']:.1f}%")
        print()
        
        # Step 4: Load to Azure ADLS (raw container)
        print("Step 4: Loading RAW data to Azure ADLS...")
        
        raw_path = loader.load_to_raw_container(df_original, file_prefix="nyc_311_test")
        
        if raw_path:
            print(f"   ✓ Successfully uploaded to raw container")
            print(f"     - Path: {raw_path}")
        else:
            print("   ✗ Failed to upload to raw container")
            return False
        print()
        
        # Step 5: Load to Azure ADLS (processed container)
        print("Step 5: Loading PROCESSED data to Azure ADLS...")
        
        processed_path = loader.load_to_processed_container(df_transformed, file_prefix="nyc_311_test")
        
        if processed_path:
            print(f"   ✓ Successfully uploaded to processed container")
            print(f"     - Path: {processed_path}")
        else:
            print("   ✗ Failed to upload to processed container")
            return False
        print()
        
        # Step 6: Summary
        print("="*60)
        print("  ✓ ETL PIPELINE TEST COMPLETED SUCCESSFULLY!")
        print("="*60)
        print()
        print("Pipeline Summary:")
        print(f"  • Extracted: {len(df_raw)} records")
        print(f"  • Transformed: {len(df_transformed)} records")
        print(f"  • Loaded to raw: ✓")
        print(f"  • Loaded to processed: ✓")
        print()
        print("Data Flow:")
        print(f"  NYC 311 API → Extract → Transform → ADLS raw → ADLS processed")
        print()
        print("Azure Resources:")
        print(f"  • Storage Account: {loader.storage_account}")
        print(f"  • Raw Container: {loader.raw_container}")
        print(f"  • Processed Container: {loader.processed_container}")
        print()
        print("Next Steps:")
        print("  1. Verify files in Azure Portal (Storage Browser)")
        print("  2. Create ADF pipeline to copy processed data to SQL")
        print("  3. Test ADF pipeline trigger (requires pipeline creation)")
        print("  4. Deploy to Airflow for scheduling")
        print()
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ ETL PIPELINE TEST FAILED: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_complete_etl_pipeline()
    sys.exit(0 if success else 1)
