"""Check files in ADLS processed container"""
import os
import sys

# Load environment variables
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'astro-airflow'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'astro-airflow', '.env'))

from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import ClientSecretCredential

def check_processed_files():
    """Check what files exist in processed container"""
    
    # Create credential
    credential = ClientSecretCredential(
        tenant_id=os.getenv('AZURE_TENANT_ID'),
        client_id=os.getenv('AZURE_CLIENT_ID'),
        client_secret=os.getenv('AZURE_CLIENT_SECRET')
    )
    
    # Create DataLake client
    account_name = os.getenv('ADLS_ACCOUNT_NAME')
    service_client = DataLakeServiceClient(
        account_url=f"https://{account_name}.dfs.core.windows.net",
        credential=credential
    )
    
    # Get file system
    file_system_client = service_client.get_file_system_client("processed")
    
    print("=" * 60)
    print("FILES IN PROCESSED CONTAINER")
    print("=" * 60)
    
    paths = file_system_client.get_paths()
    files = [p for p in paths if not p.is_directory]
    
    if not files:
        print("❌ No files found in processed container!")
        return False
    
    print(f"\nFound {len(files)} file(s):\n")
    for file in files:
        size_mb = file.content_length / (1024 * 1024)
        print(f"  ✓ {file.name}")
        print(f"    Size: {size_mb:.2f} MB ({file.content_length:,} bytes)")
        print(f"    Modified: {file.last_modified}")
        print()
    
    return True

if __name__ == "__main__":
    check_processed_files()
