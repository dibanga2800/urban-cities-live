import pandas as pd
from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import DefaultAzureCredential
import io

credential = DefaultAzureCredential()
service_client = DataLakeServiceClient(
    account_url='https://urbancitiesadls2025.dfs.core.windows.net', 
    credential=credential
)

fs_client = service_client.get_file_system_client('processed')
paths = list(fs_client.get_paths(path='processed-data'))
latest = sorted([p for p in paths if p.name.endswith('.parquet')], key=lambda x: x.name, reverse=True)[0]

print(f'Reading file: {latest.name}')

file_client = fs_client.get_file_client(latest.name)
data = file_client.download_file().readall()
df = pd.read_parquet(io.BytesIO(data))

print(f'\n=== DATETIME COLUMN TYPES ===')
for col in ['created_date', 'closed_date', 'processed_at']:
    if col in df.columns:
        print(f'{col}: {df[col].dtype}')

print(f'\n=== SAMPLE VALUES ===')
for i in range(min(5, len(df))):
    created = df.iloc[i]['created_date']
    closed = df.iloc[i]['closed_date']
    processed = df.iloc[i]['processed_at']
    print(f'Row {i}:')
    print(f'  created_date: {repr(created)} (type: {type(created).__name__})')
    print(f'  closed_date: {repr(closed)} (type: {type(closed).__name__})')
    print(f'  processed_at: {repr(processed)} (type: {type(processed).__name__})')

print(f'\n=== NULL VALUE CHECK ===')
print(f'created_date nulls: {df["created_date"].isna().sum()}')
print(f'closed_date nulls: {df["closed_date"].isna().sum()}')
print(f'processed_at nulls: {df["processed_at"].isna().sum()}')
