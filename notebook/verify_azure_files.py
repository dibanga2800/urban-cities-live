"""
Verify Azure ADLS Files
Checks that the test files were uploaded successfully to both containers
"""
import os
from datetime import datetime
from azure.identity import ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_azure_files():
    """Verify uploaded files in Azure ADLS containers"""
    
    print("\n" + "="*60)
    print("  AZURE ADLS FILE VERIFICATION")
    print("="*60 + "\n")
    
    # Get credentials
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    storage_account = os.getenv('ADLS_ACCOUNT_NAME', 'urbancitiesadls2025')
    
    # Create credential
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Create service client
    account_url = f"https://{storage_account}.dfs.core.windows.net"
    service_client = DataLakeServiceClient(account_url=account_url, credential=credential)
    
    # Check RAW container
    print("Step 1: Checking RAW container...")
    raw_fs = service_client.get_file_system_client("raw")
    
    # Check all paths in raw container
    try:
        raw_paths = raw_fs.get_paths()
        raw_files = []
        all_raw_count = 0
        
        for path in raw_paths:
            if not path.is_directory:
                all_raw_count += 1
                if 'nyc_311' in path.name:
                    raw_files.append({
                        'name': path.name,
                        'size': path.content_length,
                        'modified': path.last_modified
                    })
        
        print(f"   Total files in container: {all_raw_count}")
    except Exception as e:
        print(f"   Error listing raw container: {e}")
        raw_files = []
    
    if raw_files:
        print(f"   ✓ Found {len(raw_files)} test file(s) in raw container:")
        for file in raw_files[:5]:  # Show max 5
            size_kb = file['size'] / 1024
            print(f"     • {file['name']}")
            print(f"       Size: {file['size']} bytes ({size_kb:.2f} KB)")
            print(f"       Modified: {file['modified']}")
    else:
        print("   ✗ No test files found in raw container")
    
    # Check PROCESSED container
    print("\nStep 2: Checking PROCESSED container...")
    processed_fs = service_client.get_file_system_client("processed")
    
    # Check all paths in processed container
    try:
        processed_paths = processed_fs.get_paths()
        processed_files = []
        all_processed_count = 0
        
        for path in processed_paths:
            if not path.is_directory:
                all_processed_count += 1
                if 'nyc_311' in path.name:
                    processed_files.append({
                        'name': path.name,
                        'size': path.content_length,
                        'modified': path.last_modified
                    })
        
        print(f"   Total files in container: {all_processed_count}")
    except Exception as e:
        print(f"   Error listing processed container: {e}")
        processed_files = []
    
    if processed_files:
        print(f"   ✓ Found {len(processed_files)} test file(s) in processed container:")
        for file in processed_files[:5]:  # Show max 5
            size_kb = file['size'] / 1024
            print(f"     • {file['name']}")
            print(f"       Size: {file['size']} bytes ({size_kb:.2f} KB)")
            print(f"       Modified: {file['modified']}")
    else:
        print("   ✗ No test files found in processed container")
    
    # Summary
    print("\n" + "="*60)
    print("  VERIFICATION SUMMARY")
    print("="*60)
    print(f"  Storage Account: {storage_account}")
    print(f"  Raw Container: {len(raw_files)} test file(s)")
    print(f"  Processed Container: {len(processed_files)} test file(s)")
    
    if raw_files and processed_files:
        print("\n  ✓ All files verified successfully!")
        print("\n  Latest uploads:")
        if raw_files:
            latest_raw = max(raw_files, key=lambda x: x['modified'])
            print(f"    Raw: {latest_raw['name'].split('/')[-1]}")
        if processed_files:
            latest_processed = max(processed_files, key=lambda x: x['modified'])
            print(f"    Processed: {latest_processed['name'].split('/')[-1]}")
    else:
        print("\n  ⚠ Some files missing - check upload process")
    
    print("="*60 + "\n")
    
    return len(raw_files) > 0 and len(processed_files) > 0

if __name__ == "__main__":
    try:
        success = verify_azure_files()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
