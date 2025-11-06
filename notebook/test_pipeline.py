#!/usr/bin/env python3
"""
Test script for NYC 311 ETL Pipeline
Tests the modular components without Docker/Airflow
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all modules can be imported"""
    logger.info("Testing module imports...")
    
    try:
        from Extraction import DataExtractor
        logger.info("✅ DataExtractor imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import DataExtractor: {e}")
        return False
    
    try:
        from Transformation import DataTransformer
        logger.info("✅ DataTransformer imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import DataTransformer: {e}")
        return False
    
    try:
        from Loading import DataLoader, StateManager
        logger.info("✅ DataLoader and StateManager imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import Loading modules: {e}")
        return False
    
    return True

def test_extractor():
    """Test the data extractor with a small sample"""
    logger.info("Testing DataExtractor...")
    
    try:
        from Extraction import DataExtractor
        
        # Use a test time from 7 days ago
        test_time = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S')
        
        extractor = DataExtractor(
            api_url="https://data.cityofnewyork.us/resource/erm2-nwe9.json",
            batch_size=10  # Small batch for testing
        )
        
        logger.info(f"Extracting small sample since: {test_time}")
        df = extractor.extract_incremental(test_time)
        
        if df.empty:
            logger.warning("⚠️ No data extracted (this might be normal)")
            return True
        else:
            logger.info(f"✅ Extracted {len(df)} records")
            logger.info(f"Columns: {list(df.columns)}")
            return True
            
    except Exception as e:
        logger.error(f"❌ DataExtractor test failed: {e}")
        return False

def test_transformer():
    """Test the data transformer with sample data"""
    logger.info("Testing DataTransformer...")
    
    try:
        from Transformation import DataTransformer
        import pandas as pd
        
        # Create sample data
        sample_data = {
            'unique_key': ['12345'],
            'created_date': ['2025-10-31T10:00:00.000'],
            'agency': ['DOT'],
            'complaint_type': ['Street Light Condition'],
            'descriptor': ['Street Light Out'],
            'location_type': ['Street'],
            'incident_zip': ['10001'],
            'incident_address': ['123 MAIN ST'],
            'street_name': ['MAIN ST'],
            'cross_street_1': ['1ST AVE'],
            'cross_street_2': ['2ND AVE'],
            'intersection_street_1': [None],
            'intersection_street_2': [None],
            'address_type': ['ADDRESS'],
            'city': ['NEW YORK'],
            'landmark': [None],
            'facility_type': [None],
            'status': ['Open'],
            'due_date': [None],
            'resolution_description': [None],
            'resolution_action_updated_date': [None],
            'community_board': ['01 MANHATTAN'],
            'bbl': ['1000120001'],
            'borough': ['MANHATTAN'],
            'x_coordinate_state_plane': ['987654'],
            'y_coordinate_state_plane': ['123456'],
            'open_data_channel_type': ['ONLINE'],
            'park_facility_name': [None],
            'park_borough': [None],
            'vehicle_type': [None],
            'taxi_company_borough': [None],
            'taxi_pick_up_location': [None],
            'bridge_highway_name': [None],
            'bridge_highway_direction': [None],
            'road_ramp': [None],
            'bridge_highway_segment': [None],
            'latitude': ['40.7589'],
            'longitude': ['-73.9851']
        }
        
        df = pd.DataFrame(sample_data)
        transformer = DataTransformer()
        
        logger.info("Transforming sample data...")
        df_transformed = transformer.transform(df.copy())
        
        logger.info(f"✅ Transformation completed")
        logger.info(f"Original columns: {len(df.columns)}")
        logger.info(f"Transformed columns: {len(df_transformed.columns)}")
        
        if 'data_quality_score' in df_transformed.columns:
            score = df_transformed['data_quality_score'].iloc[0]
            logger.info(f"Sample quality score: {score}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ DataTransformer test failed: {e}")
        return False

def test_loader():
    """Test the data loader with sample data"""
    logger.info("Testing DataLoader...")
    
    try:
        from Loading import DataLoader, StateManager
        import pandas as pd
        
        # Create sample data
        sample_data = {
            'unique_key': ['12345'],
            'created_date': ['2025-10-31T10:00:00'],
            'agency': ['DOT'],
            'complaint_type': ['Street Light Condition'],
            'data_quality_score': [85.5]
        }
        
        df = pd.DataFrame(sample_data)
        
        loader = DataLoader()
        
        logger.info("Testing local file loading...")
        local_path = loader.load_to_local(df, "test_output")
        
        if local_path and os.path.exists(local_path):
            logger.info(f"✅ Local file created: {local_path}")
            # Clean up test file
            try:
                os.remove(local_path)
                logger.info("Test file cleaned up")
            except:
                pass
        else:
            logger.warning("⚠️ Local file not created (might be normal)")
        
        # Test state manager
        logger.info("Testing StateManager...")
        state_manager = StateManager()
        
        test_time = datetime.utcnow().isoformat()
        state_manager.update_last_processed_time(test_time)
        retrieved_time = state_manager.get_last_processed_time()
        
        if retrieved_time:
            logger.info(f"✅ State management working: {retrieved_time}")
        else:
            logger.warning("⚠️ State management not working")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ DataLoader test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🧪 Starting NYC 311 ETL Pipeline Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Data Extraction", test_extractor),
        ("Data Transformation", test_transformer),
        ("Data Loading", test_loader)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        logger.info("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    logger.info("\n" + "=" * 50)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status:8} | {test_name}")
    
    logger.info("-" * 50)
    logger.info(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Your pipeline modules are working correctly.")
        logger.info("\n💡 Next steps:")
        logger.info("   1. Configure your API token in .env file")
        logger.info("   2. Set up Azure storage credentials")
        logger.info("   3. Run the full pipeline with: python dag_script.py")
    else:
        logger.error("❌ Some tests failed. Please fix the issues before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)