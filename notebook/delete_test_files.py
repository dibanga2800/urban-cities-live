"""
Delete old test files from ADLS processed container
This will allow ADF pipeline to run successfully without duplicate key errors
"""
from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient
import os
from dotenv import load_dotenv

load_dotenv()

# Azure configuration
storage_account_name = "urbancitiesadls2025"
container_name = "processed"
folder_path = "processed-data"

print("=" * 70)
print("  DELETE OLD TEST FILES FROM ADLS")
print("=" * 70)
print(f"Storage Account: {storage_account_name}")
print(f"Container: {container_name}")
print(f"Folder: {folder_path}\n")

try:
    # Use default credential (will use environment variables)
    credential = DefaultAzureCredential()
    
    # Create service client
    service_client = DataLakeServiceClient(
        account_url=f"https://{storage_account_name}.dfs.core.windows.net",
        credential=credential
    )
    
    # Get filesystem client
    file_system_client = service_client.get_file_system_client(container_name)
    
    # List all files
    print("Scanning for test files...")
    paths = file_system_client.get_paths(path=folder_path)
    
    test_files = []
    for path in paths:
        if not path.is_directory and 'e2e_test' in path.name:
            test_files.append(path)
    
    if not test_files:
        print("✓ No test files found. Container is clean.\n")
    else:
        print(f"Found {len(test_files)} test file(s) to delete:\n")
        
        for i, file in enumerate(test_files, 1):
            print(f"{i}. {file.name}")
            print(f"   Size: {file.content_length} bytes")
            print(f"   Modified: {file.last_modified}")
            
            # Delete the file
            file_client = file_system_client.get_file_client(file.name)
            file_client.delete_file()
            print(f"   ✓ Deleted\n")
        
        print(f"✓ Successfully deleted {len(test_files)} test file(s)")
    
    print("\n" + "=" * 70)
    print("  ✓ CLEANUP COMPLETED!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
