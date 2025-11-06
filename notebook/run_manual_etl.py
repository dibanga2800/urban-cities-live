"""
Manual ETL Pipeline Execution (Same as Airflow DAG)
This simulates what the Airflow DAG does, including the new ADF trigger
"""
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import ETL modules
from Extraction import DataExtractor
from Transformation import DataTransformer
from Loading_Azure import AzureDataLoader

# State file
STATE_FILE = 'data/etl_state.json'

def load_state():
    """Load last processed timestamp"""
    import json
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                return state.get('last_processed_time')
    except Exception as e:
        print(f"Error loading state: {e}")
    return (datetime.now() - timedelta(days=1)).isoformat()

def save_state(timestamp):
    """Save last processed timestamp"""
    import json
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump({
                'last_processed_time': timestamp,
                'updated_at': datetime.now().isoformat()
            }, f, indent=2)
        print(f"✓ State saved: {timestamp}")
    except Exception as e:
        print(f"Error saving state: {e}")

def main():
    print("\n" + "=" * 80)
    print("  MANUAL ETL PIPELINE EXECUTION (WITH ADF TRIGGER)")
    print("=" * 80)
    
    # STEP 1: EXTRACT
    print("\n[1/5] EXTRACTING DATA FROM NYC 311 API")
    print("-" * 80)
    
    last_processed = load_state()
    print(f"Extracting data since: {last_processed}")
    
    api_url = os.getenv("NYC_311_API_URL", "https://data.cityofnewyork.us/resource/erm2-nwe9.json")
    extractor = DataExtractor(api_url=api_url)
    df_raw = extractor.extract_incremental(since_time=last_processed)
    
    print(f"✓ Extracted {len(df_raw)} records")
    if len(df_raw) > 0:
        print(f"  Date range: {df_raw['created_date'].min()} to {df_raw['created_date'].max()}")
    else:
        print("⚠ No new data found. Exiting.")
        return
    
    # STEP 2: TRANSFORM
    print("\n[2/5] TRANSFORMING DATA")
    print("-" * 80)
    
    transformer = DataTransformer()
    df_transformed = transformer.transform(df_raw)
    
    summary = transformer.get_transformation_summary(df_raw, df_transformed)
    print(f"✓ Transformed {len(df_transformed)} records")
    print(f"  Quality Score: {summary['avg_quality_score']:.1f}%")
    print(f"  Records with Location: {summary['records_with_location']}")
    print(f"  Closed Complaints: {summary['closed_complaints']}")
    
    # STEP 3: LOAD TO AZURE ADLS
    print("\n[3/5] LOADING DATA TO AZURE DATA LAKE")
    print("-" * 80)
    
    loader = AzureDataLoader()
    
    print("Uploading to raw container...")
    raw_path = loader.load_to_raw_container(df_raw, file_prefix="nyc_311_manual")
    print(f"✓ Raw data uploaded: {raw_path}")
    
    print("\nUploading to processed container...")
    processed_path = loader.load_to_processed_container(df_transformed, file_prefix="nyc_311_manual")
    print(f"✓ Processed data uploaded: {processed_path}")
    
    # STEP 4: TRIGGER AZURE DATA FACTORY (NEW!)
    print("\n[4/5] TRIGGERING AZURE DATA FACTORY PIPELINE")
    print("-" * 80)
    print("🆕 This is the new step that copies data from ADLS to SQL Database!")
    
    adf_result = loader.trigger_adf_pipeline(
        pipeline_name="CopyProcessedDataToSQL",
        source_file_path=processed_path
    )
    
    print(f"\n✓ ADF Pipeline Result:")
    print(f"  Run ID: {adf_result.get('run_id')}")
    print(f"  Status: {adf_result.get('status')}")
    print(f"  Duration: {adf_result.get('duration_ms')} ms")
    
    if adf_result.get('status') == 'Succeeded':
        print("  🎉 Data successfully copied to SQL Database!")
    else:
        print(f"  ⚠ Warning: Pipeline status: {adf_result.get('status')}")
        print(f"  Message: {adf_result.get('message')}")
    
    # STEP 5: UPDATE STATE
    print("\n[5/5] UPDATING ETL STATE")
    print("-" * 80)
    
    if len(df_transformed) > 0 and 'created_date' in df_transformed.columns:
        latest_timestamp = df_transformed['created_date'].max()
        save_state(latest_timestamp)
    
    # SUMMARY
    print("\n" + "=" * 80)
    print("  PIPELINE EXECUTION COMPLETED!")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"  • Records Extracted: {len(df_raw)}")
    print(f"  • Records Transformed: {len(df_transformed)}")
    print(f"  • Quality Score: {summary['avg_quality_score']:.1f}%")
    print(f"  • ADF Status: {adf_result.get('status')}")
    print(f"  • Raw File: {raw_path}")
    print(f"  • Processed File: {processed_path}")
    print(f"\n✅ Next: Check SQL Database for new records")
    print(f"   Command: python verify_sql_data.py")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Pipeline interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
