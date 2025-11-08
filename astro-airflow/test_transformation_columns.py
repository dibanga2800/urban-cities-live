"""
Test script to verify transformation produces all 20 expected columns
"""
import sys
sys.path.insert(0, 'C:\\Users\\David Ibanga\\Data Engineering practicals\\Urban_Cities_live_Service\\astro-airflow\\include')

from Transformation import DataTransformer
import pandas as pd
from datetime import datetime

# Sample data with null closed_date
sample_data = {
    'unique_key': ['12345678'],
    'created_date': ['2025-01-15 10:30:00'],
    'closed_date': [None],  # Null to test resolution_hours creation
    'agency': ['NYPD'],
    'complaint_type': ['Noise - Street/Sidewalk'],
    'descriptor': ['Loud Music/Party'],
    'borough': ['BROOKLYN'],
    'status': ['Open'],
    'latitude': [40.6782],
    'longitude': [-73.9442]
}

df = pd.DataFrame(sample_data)
print("Input DataFrame:")
print(df)
print(f"\nInput columns ({len(df.columns)}): {list(df.columns)}")

# Transform
transformer = DataTransformer()
transformed_df = transformer.transform(df)

print(f"\n\nOutput DataFrame:")
print(transformed_df)
print(f"\nOutput columns ({len(transformed_df.columns)}): {list(transformed_df.columns)}")

# Expected columns
expected_columns = [
    'unique_key', 'created_date', 'closed_date', 'agency', 'complaint_type',
    'descriptor', 'borough', 'status', 'latitude', 'longitude', 'created_year',
    'created_month', 'created_day', 'created_hour', 'created_weekday',
    'resolution_hours', 'is_closed', 'has_location', 'processed_at',
    'data_quality_score'
]

print(f"\n\nExpected columns ({len(expected_columns)}): {expected_columns}")

# Check for missing columns
missing_columns = [col for col in expected_columns if col not in transformed_df.columns]
extra_columns = [col for col in transformed_df.columns if col not in expected_columns]

if missing_columns:
    print(f"\n❌ MISSING COLUMNS: {missing_columns}")
else:
    print(f"\n✅ All expected columns present!")

if extra_columns:
    print(f"⚠️  EXTRA COLUMNS: {extra_columns}")

# Check column order
if list(transformed_df.columns) == expected_columns:
    print("✅ Column order matches SQL schema exactly!")
else:
    print("⚠️  Column order differs from expected:")
    for i, (actual, expected) in enumerate(zip(transformed_df.columns, expected_columns)):
        if actual != expected:
            print(f"   Position {i}: got '{actual}', expected '{expected}'")

# Check resolution_hours
print(f"\n\nresolution_hours column:")
print(f"  Value: {transformed_df['resolution_hours'].iloc[0]}")
print(f"  Type: {type(transformed_df['resolution_hours'].iloc[0])}")
print(f"  Is null: {pd.isna(transformed_df['resolution_hours'].iloc[0])}")
