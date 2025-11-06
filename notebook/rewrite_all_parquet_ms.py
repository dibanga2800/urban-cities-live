"""
Rewrite all Parquet files in ADLS processed-data to ensure timestamps are encoded
with millisecond precision (TIMESTAMP_MILLIS), which ADF maps cleanly to SQL DateTime.
For each processed-data/*.parquet that doesn't already end with _ms.parquet, this script
creates a sibling file with suffix _ms.parquet.

Auth: Uses the resilient AzureDataLoader credential fallback (SP -> Azure CLI -> Default).
"""
import io
import os
from typing import List

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from Loading_Azure import AzureDataLoader


def list_processed_parquet_files(loader: AzureDataLoader) -> List[str]:
    fs = loader.datalake_client.get_file_system_client(loader.processed_container)
    paths = list(fs.get_paths(path="processed-data"))
    return [p.name for p in paths if (not p.is_directory and p.name.endswith('.parquet'))]


def rewrite_to_ms(loader: AzureDataLoader, path: str) -> str:
    """Download Parquet at path, coerce timestamps to ms and upload as _ms variant. Returns new path."""
    fs = loader.datalake_client.get_file_system_client(loader.processed_container)
    file_client = fs.get_file_client(path)
    data = file_client.download_file().readall()

    table = pq.read_table(io.BytesIO(data))
    pdf = table.to_pandas()
    # Normalize likely datetime columns
    for col in [c for c in ['created_date', 'closed_date', 'processed_at'] if c in pdf.columns]:
        dtype = str(pdf[col].dtype)
        if dtype.startswith('int'):
            # Treat as epoch nanoseconds
            pdf[col] = pd.to_datetime(pdf[col], unit='ns', errors='coerce')
        else:
            try:
                pdf[col] = pd.to_datetime(pdf[col], errors='coerce')
            except Exception:
                pass

    out_table = pa.Table.from_pandas(pdf, preserve_index=False)
    buf = io.BytesIO()
    pq.write_table(out_table, buf, coerce_timestamps='ms', allow_truncated_timestamps=True)
    new_bytes = buf.getvalue()

    base = os.path.basename(path)
    root, ext = os.path.splitext(base)
    new_name = f"processed-data/{root}_ms{ext}"
    new_client = fs.get_file_client(new_name)
    new_client.upload_data(new_bytes, overwrite=True)
    return new_name


def main():
    loader = AzureDataLoader()
    files = list_processed_parquet_files(loader)
    # Filter to non-ms files
    candidates = [p for p in files if not p.endswith('_ms.parquet')]
    if not candidates:
        print("No non-ms parquet files found; nothing to rewrite.")
        return

    print(f"Found {len(candidates)} parquet file(s) to rewrite to ms precision:")
    for p in candidates:
        print(f"  - {p}")

    rewritten = []
    for p in candidates:
        try:
            new_path = rewrite_to_ms(loader, p)
            rewritten.append(new_path)
            print(f"✓ Rewrote {p} -> {new_path}")
        except Exception as e:
            print(f"✗ Failed to rewrite {p}: {e}")

    print("\nSummary:")
    print(f"  Rewritten: {len(rewritten)}")
    for p in rewritten:
        print(f"    • {p}")


if __name__ == "__main__":
    main()
