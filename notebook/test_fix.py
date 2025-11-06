#!/usr/bin/env python3

from Extraction import DataExtractor
from Transformation import DataTransformer
from Loading import DataLoader, StateManager

def test_pipeline():
    # Initialize components
    state = StateManager()
    extractor = DataExtractor()
    transformer = DataTransformer()
    loader = DataLoader()
    
    # Test extraction
    df = extractor.extract_incremental(state.get_last_processed_time())
    print(f'Extracted: {len(df)} records')
    print(f'Original columns: {list(df.columns)}')
    
    # Test transformation
    df_transformed = transformer.transform(df)
    print(f'Transformed successfully: {len(df_transformed)} records')
    print(f'Has closed_date after transform: {"closed_date" in df_transformed.columns}')
    print(f'Final columns: {list(df_transformed.columns)}')
    
    return True

if __name__ == "__main__":
    try:
        result = test_pipeline()
        print("✅ Pipeline test successful!")
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()