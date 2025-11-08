"""
Quick script to check Parquet file columns in ADLS
"""
import os
import pandas as pd
from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import ClientSecretCredential

"""
Credentials are required via environment variables:
    - AZURE_TENANT_ID
    - AZURE_CLIENT_ID
    - AZURE_CLIENT_SECRET
No hardcoded defaults are provided to avoid accidental secret leaks.
"""

# Azure credentials (must be provided via environment variables)
tenant_id = os.environ.get('AZURE_TENANT_ID')
client_id = os.environ.get('AZURE_CLIENT_ID')
client_secret = os.environ.get('AZURE_CLIENT_SECRET')
storage_account = os.environ.get('AZURE_STORAGE_ACCOUNT_NAME', 'urbancitiesadls2025')

if not all([tenant_id, client_id, client_secret]):
        raise RuntimeError(
                "Missing Azure credentials. Please set AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET in your environment."
        )

# Create credential
credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=client_secret
)

# Create Data Lake client
account_url = f"https://{storage_account}.dfs.core.windows.net"
datalake_client = DataLakeServiceClient(account_url=account_url, credential=credential)

# Get processed container
fs = datalake_client.get_file_system_client('processed')

# List parquet files
paths = list(fs.get_paths(path="processed-data"))
parquet_files = [p for p in paths if (not p.is_directory and p.name.endswith('.parquet'))]
parquet_files.sort(key=lambda p: p.last_modified, reverse=True)

print(f"Found {len(parquet_files)} parquet files")
print("\nMost recent files:")
for i, pf in enumerate(parquet_files[:5]):
    print(f"{i+1}. {os.path.basename(pf.name)} - {pf.last_modified}")

if parquet_files:
    # Download and read the most recent file
    latest_file = parquet_files[0]
    file_name = os.path.basename(latest_file.name)
    
    print(f"\n{'='*60}")
    print(f"Reading most recent file: {file_name}")
    print(f"{'='*60}")
    
    # Download file
    file_client = fs.get_file_client(latest_file.name)
    download = file_client.download_file()
    downloaded_bytes = download.readall()
    
    # Save temporarily and read with pandas
    temp_file = 'temp_check.parquet'
    with open(temp_file, 'wb') as f:
        f.write(downloaded_bytes)
    
    # Read parquet
    df = pd.read_parquet(temp_file)
    
    print(f"\nRows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print("\nColumn names:")
    for i, col in enumerate(df.columns, 1):
        dtype = df[col].dtype
        non_null = df[col].notna().sum()
        print(f"  {i:2d}. {col:25s} - dtype: {str(dtype):15s} - non-null: {non_null}/{len(df)}")
    
    print("\n" + "="*60)
    print("Sample data (first row):")
    print("="*60)
    for col in df.columns:
        value = df[col].iloc[0] if len(df) > 0 else None
        print(f"  {col:25s}: {value}")
    
    # Clean up
    os.remove(temp_file)
    print(f"\n✓ Analysis complete")
