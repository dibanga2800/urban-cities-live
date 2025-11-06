"""
Rewrite the latest Parquet in ADLS processed-data to ensure timestamps are encoded
with millisecond precision (TIMESTAMP_MILLIS), which ADF maps cleanly to SQL DateTime.
Outputs a new file with suffix `_ms.parquet` and prints the fileName for pipeline use.
"""
import os
import io
from datetime import timezone
from dotenv import load_dotenv
load_dotenv()
import pandas as pd

from azure.identity import ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
import pyarrow.parquet as pq
import pyarrow as pa

ACCOUNT = os.getenv('ADLS_ACCOUNT_NAME', 'urbancitiesadls2025')
TENANT = os.getenv('AZURE_TENANT_ID', 'edc41ca9-a02a-4623-97cb-2a58f19e3c46')
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
CONTAINER = 'processed'
FOLDER = 'processed-data'

assert CLIENT_ID and CLIENT_SECRET, 'AZURE_CLIENT_ID/SECRET not configured'

cred = ClientSecretCredential(tenant_id=TENANT, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
svc = DataLakeServiceClient(account_url=f"https://{ACCOUNT}.dfs.core.windows.net", credential=cred)
fs = svc.get_file_system_client(CONTAINER)

# Find latest parquet
paths = [p for p in fs.get_paths(path=FOLDER) if (not p.is_directory and p.name.endswith('.parquet'))]
paths.sort(key=lambda p: p.last_modified, reverse=True)
if not paths:
    raise SystemExit('No parquet files found in processed-data')
latest = paths[0]

# Download
file_client = fs.get_file_client(latest.name)
content = file_client.download_file().readall()

# Read and re-write with ms timestamps
source = pq.read_table(io.BytesIO(content))
# Rebuild via pandas to normalize any object dtypes and convert epoch ns to datetime
pdf = source.to_pandas()
for col in [c for c in ['created_date','closed_date','processed_at'] if c in pdf.columns]:
    if str(pdf[col].dtype).startswith('int'):
        # Treat as epoch nanoseconds
        pdf[col] = pd.to_datetime(pdf[col], unit='ns', errors='coerce')
    else:
        # Attempt generic to_datetime for strings
        try:
            pdf[col] = pd.to_datetime(pdf[col], errors='coerce')
        except Exception:
            pass
new_table = pa.Table.from_pandas(pdf, preserve_index=False)
buf = io.BytesIO()
pq.write_table(new_table, buf, coerce_timestamps='ms', allow_truncated_timestamps=True)
new_bytes = buf.getvalue()

# Upload new file
base = os.path.basename(latest.name)
root, ext = os.path.splitext(base)
new_name = f"{FOLDER}/{root}_ms{ext}"
new_client = fs.get_file_client(new_name)
new_client.upload_data(new_bytes, overwrite=True)

print({'fileName': os.path.basename(new_name), 'lastModified': latest.last_modified.astimezone(timezone.utc).isoformat()})
