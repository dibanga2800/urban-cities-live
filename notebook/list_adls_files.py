"""
List files in ADLS processed container
"""
from azure.identity import ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
import os

# Azure credentials
tenant_id = "edc41ca9-a02a-4623-97cb-2a58f19e3c46"
client_id = "27b470a2-fa5d-458a-85d5-e639c0791f23"
client_secret = os.environ.get('AZURE_CLIENT_SECRET', 'SUy8Q~XqJk1v2LBfWN3kJnS4A6Zr9Ht_Dp5Cm7Eq')
storage_account_name = "urbancitiesadls2025"

print("=" * 70)
print("  LIST ADLS PROCESSED FILES")
print("=" * 70)

try:
    # Authenticate
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Create service client
    service_client = DataLakeServiceClient(
        account_url=f"https://{storage_account_name}.dfs.core.windows.net",
        credential=credential
    )
    
    # Get filesystem client
    file_system_client = service_client.get_file_system_client("processed")
    
    # List files in processed-data folder
    print("\nFiles in processed-data folder:\n")
    paths = file_system_client.get_paths(path="processed-data")
    
    files = []
    for path in paths:
        if not path.is_directory:
            files.append(path)
    
    if files:
        print(f"Found {len(files)} file(s):\n")
        for i, file in enumerate(files, 1):
            print(f"{i}. {file.name}")
            print(f"   Size: {file.content_length} bytes")
            print(f"   Modified: {file.last_modified}")
            print()
    else:
        print("No files found.\n")
    
    print("=" * 70)
    print("  ✓ LISTING COMPLETED!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
