"""
Test Azure Connection
Quick test to verify Azure Data Lake and Data Factory connectivity
"""

import os
import sys
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our Azure loader
from Loading_Azure import AzureDataLoader

def test_azure_connection():
    """Test Azure connectivity and configuration"""
    
    print("\n" + "="*60)
    print("  TESTING AZURE CONNECTION")
    print("="*60 + "\n")
    
    try:
        # 1. Test initialization
        print("1. Initializing Azure Data Loader...")
        loader = AzureDataLoader()
        print("   ✓ Azure Data Loader initialized successfully\n")
        
        # 2. Create test data
        print("2. Creating test data...")
        test_data = pd.DataFrame({
            'test_id': [1, 2, 3],
            'timestamp': [datetime.now()] * 3,
            'message': ['Test message 1', 'Test message 2', 'Test message 3']
        })
        print(f"   ✓ Created test DataFrame with {len(test_data)} records\n")
        
        # 3. Test upload to raw container
        print("3. Testing upload to ADLS raw container...")
        raw_path = loader.load_to_raw_container(test_data, file_prefix="test")
        if raw_path:
            print(f"   ✓ Successfully uploaded to: {raw_path}\n")
        else:
            print("   ✗ Failed to upload to raw container\n")
            return False
        
        # 4. Test upload to processed container
        print("4. Testing upload to ADLS processed container...")
        processed_path = loader.load_to_processed_container(test_data, file_prefix="test")
        if processed_path:
            print(f"   ✓ Successfully uploaded to: {processed_path}\n")
        else:
            print("   ✗ Failed to upload to processed container\n")
            return False
        
        # 5. Display configuration
        print("5. Azure Configuration:")
        print(f"   Storage Account: {loader.storage_account}")
        print(f"   Subscription ID: {loader.subscription_id}")
        print(f"   Resource Group: {loader.resource_group}")
        print(f"   ADF Name: {loader.adf_name}")
        print(f"   Containers: {loader.raw_container}, {loader.processed_container}, {loader.curated_container}")
        
        print("\n" + "="*60)
        print("  ✓ ALL TESTS PASSED!")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_azure_connection()
    sys.exit(0 if success else 1)
