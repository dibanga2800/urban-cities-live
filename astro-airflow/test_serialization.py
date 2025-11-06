import pandas as pd
import json

# Test DataFrame with string dtypes and JSON serialization
test_df = pd.DataFrame({
    'unique_key': [1, 2, 3],
    'created_date': ['2025-01-01 10:00:00', '2025-01-02 11:00:00', '2025-01-03 12:00:00'],
    'closed_date': ['2025-01-01 15:00:00', '', '2025-01-03 16:00:00'],
    'complaint_type': ['Noise', 'Heating', 'Water']
})

print('Original DataFrame dtypes:')
for col in test_df.columns:
    print(f'  {col}: {test_df[col].dtype}')

# Convert datetime columns to string dtype
datetime_cols = ['created_date', 'closed_date']
for col in datetime_cols:
    test_df[col] = test_df[col].astype('string')

print('\nAfter string conversion:')
for col in test_df.columns:
    print(f'  {col}: {test_df[col].dtype}')

# Test JSON serialization with different approaches
print('\n=== Testing JSON serialization ===')

# Method 1: to_json with records orient
try:
    json_str = test_df.to_json(orient='records')
    print('to_json(orient="records") works')

    # Test deserialization
    reconstructed = pd.read_json(json_str, orient='records')
    print('read_json works')

    print('Reconstructed dtypes:')
    for col in reconstructed.columns:
        print(f'  {col}: {reconstructed[col].dtype}')

except Exception as e:
    print(f'JSON method failed: {e}')

# Method 2: Convert to dict and back
try:
    df_dict = test_df.to_dict('records')
    json_str = json.dumps(df_dict)
    print('to_dict + json.dumps works')

    # Deserialize
    data = json.loads(json_str)
    reconstructed = pd.DataFrame(data)
    print('json.loads + DataFrame works')

    print('Reconstructed dtypes:')
    for col in reconstructed.columns:
        print(f'  {col}: {reconstructed[col].dtype}')

except Exception as e:
    print(f'Dict method failed: {e}')

# Method 3: Pickle approach (if JSON doesn't work)
try:
    import pickle
    import base64

    # Serialize with pickle
    pickled = pickle.dumps(test_df)
    encoded = base64.b64encode(pickled).decode('utf-8')
    print('Pickle + base64 encoding works')

    # Deserialize
    decoded = base64.b64decode(encoded)
    unpickled = pickle.loads(decoded)
    print('base64 decode + unpickle works')

    print('Pickle reconstructed dtypes:')
    for col in unpickled.columns:
        print(f'  {col}: {unpickled[col].dtype}')

except Exception as e:
    print(f'Pickle method failed: {e}')