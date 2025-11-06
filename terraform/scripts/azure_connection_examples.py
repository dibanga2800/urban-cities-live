# Python connection examples for Azure resources created by Terraform
# Install required packages: pip install azure-storage-file-datalake psycopg2-binary python-dotenv

import os
from dotenv import load_dotenv
from azure.storage.filedatalake import DataLakeServiceClient
import psycopg2

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# Azure Data Lake Storage (ADLS) Gen2 Connection
# =============================================================================

def get_adls_client():
    """
    Create an ADLS Gen2 client using account key authentication.
    
    After running terraform apply, get these values from:
    terraform output storage_account_name
    terraform output storage_account_primary_access_key
    """
    storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    storage_account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    
    account_url = f"https://{storage_account_name}.dfs.core.windows.net"
    
    service_client = DataLakeServiceClient(
        account_url=account_url,
        credential=storage_account_key
    )
    
    return service_client


def upload_file_to_adls(local_file_path, container_name, remote_file_path):
    """
    Upload a file to ADLS Gen2.
    
    Args:
        local_file_path: Path to local file
        container_name: ADLS container/filesystem name (e.g., 'raw', 'processed', 'curated')
        remote_file_path: Destination path in ADLS (e.g., 'nyc_311/data.csv')
    """
    service_client = get_adls_client()
    file_system_client = service_client.get_file_system_client(container_name)
    file_client = file_system_client.get_file_client(remote_file_path)
    
    with open(local_file_path, 'rb') as file:
        file_client.upload_data(file, overwrite=True)
    
    print(f"✓ Uploaded {local_file_path} to {container_name}/{remote_file_path}")


def download_file_from_adls(container_name, remote_file_path, local_file_path):
    """
    Download a file from ADLS Gen2.
    
    Args:
        container_name: ADLS container/filesystem name
        remote_file_path: Source path in ADLS
        local_file_path: Destination path on local machine
    """
    service_client = get_adls_client()
    file_system_client = service_client.get_file_system_client(container_name)
    file_client = file_system_client.get_file_client(remote_file_path)
    
    with open(local_file_path, 'wb') as file:
        download = file_client.download_file()
        file.write(download.readall())
    
    print(f"✓ Downloaded {container_name}/{remote_file_path} to {local_file_path}")


def list_files_in_adls(container_name, path=""):
    """
    List files in an ADLS container.
    
    Args:
        container_name: ADLS container/filesystem name
        path: Path within container (optional)
    """
    service_client = get_adls_client()
    file_system_client = service_client.get_file_system_client(container_name)
    
    paths = file_system_client.get_paths(path=path)
    
    print(f"Files in {container_name}/{path}:")
    for path in paths:
        print(f"  - {path.name}")


# =============================================================================
# PostgreSQL Connection
# =============================================================================

def get_postgres_connection():
    """
    Create a PostgreSQL connection.
    
    After running terraform apply, get these values from:
    terraform output postgresql_server_fqdn
    terraform output postgresql_database_name
    And the credentials from your terraform.tfvars file
    """
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=5432,
        database=os.getenv("POSTGRES_DATABASE"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        sslmode='require'
    )
    
    return conn


def execute_postgres_query(query, params=None):
    """
    Execute a PostgreSQL query.
    
    Args:
        query: SQL query to execute
        params: Query parameters (optional)
    """
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params)
        conn.commit()
        
        # If it's a SELECT query, fetch results
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            return results
        
        print("✓ Query executed successfully")
    except Exception as e:
        print(f"✗ Error executing query: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def create_sample_table():
    """
    Create a sample table in PostgreSQL.
    """
    query = """
    CREATE TABLE IF NOT EXISTS nyc_311_incidents (
        id SERIAL PRIMARY KEY,
        unique_key VARCHAR(50),
        created_date TIMESTAMP,
        agency VARCHAR(100),
        complaint_type VARCHAR(255),
        descriptor VARCHAR(255),
        location_type VARCHAR(100),
        incident_zip VARCHAR(10),
        borough VARCHAR(50),
        latitude FLOAT,
        longitude FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    execute_postgres_query(query)
    print("✓ Table created successfully")


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    print("Azure Resource Connection Examples")
    print("===================================")
    print()
    
    # Example: List ADLS containers
    try:
        print("1. Testing ADLS connection...")
        list_files_in_adls("raw")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Example: Test PostgreSQL connection
    try:
        print("2. Testing PostgreSQL connection...")
        results = execute_postgres_query("SELECT version()")
        print(f"   PostgreSQL version: {results[0][0]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    print("For more examples, see the individual function definitions above.")
