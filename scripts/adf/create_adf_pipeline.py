"""
Create Azure Data Factory Pipeline
Sets up the Copy Data pipeline from ADLS to Azure SQL Database
"""
import os
from datetime import datetime
from azure.identity import ClientSecretCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import (
    LinkedServiceResource,
    AzureSqlDatabaseLinkedService,
    AzureBlobFSLinkedService,
    DatasetResource,
    AzureSqlTableDataset,
    ParquetDataset,
    ParquetSource,
    CopyActivity,
    SqlSink,
    AzureBlobFSLocation,
    PipelineResource,
    DatasetReference,
    LinkedServiceReference,
    SecureString,
    AzureBlobFSReadSettings,
    ParameterSpecification,
    Expression,
    # Data Flow related imports
    MappingDataFlow,
    DataFlowResource,
    ExecuteDataFlowActivity,
    DataFlowReference
)
from dotenv import load_dotenv

# Load environment variables from Airflow .env file (repo-root/astro-airflow/.env)
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'astro-airflow', '.env')
load_dotenv(env_path)

def create_adf_pipeline():
    """Create ADF pipeline with linked services, datasets, and copy activity"""
    
    print("\n" + "="*60)
    print("  AZURE DATA FACTORY PIPELINE SETUP")
    print("="*60 + "\n")
    
    # Get configuration
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
    resource_group = os.getenv('ADF_RESOURCE_GROUP', 'urban-cities-rg')
    adf_name = os.getenv('ADF_NAME', 'urban-cities-adf')
    
    storage_account = os.getenv('ADLS_ACCOUNT_NAME', 'urbancitiesadls2025')
    sql_server = os.getenv('SQL_SERVER')
    sql_database = os.getenv('SQL_DATABASE')
    sql_username = os.getenv('SQL_USERNAME')
    sql_password = os.getenv('SQL_PASSWORD')
    
    print("Configuration:")
    print(f"  - Resource Group: {resource_group}")
    print(f"  - Data Factory: {adf_name}")
    print(f"  - Storage Account: {storage_account}")
    print(f"  - SQL Server: {sql_server}")
    print(f"  - SQL Database: {sql_database}\n")
    
    # Validate required auth variables
    missing = [name for name, val in {
        'AZURE_TENANT_ID': tenant_id,
        'AZURE_CLIENT_ID': client_id,
        'AZURE_CLIENT_SECRET': client_secret,
        'AZURE_SUBSCRIPTION_ID': subscription_id
    }.items() if not val]
    if missing:
        print(f"\nERROR: Missing required Azure auth environment variables: {', '.join(missing)}")
        print("Ensure astro-airflow/.env contains these values before running the script.")
        return False

    # Create credential
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Create ADF client
    adf_client = DataFactoryManagementClient(credential, subscription_id)
    
    # Step 1: Create ADLS Linked Service
    print("Step 1: Creating ADLS Gen2 Linked Service...")
    try:
        adls_linked_service = LinkedServiceResource(
            properties=AzureBlobFSLinkedService(
                url=f"https://{storage_account}.dfs.core.windows.net",
                tenant=tenant_id,
                service_principal_id=client_id,
                service_principal_key=SecureString(value=client_secret)
            )
        )
        adf_client.linked_services.create_or_update(
            resource_group,
            adf_name,
            "AzureDataLakeStorage_LinkedService",
            adls_linked_service
        )
        print("   [OK] ADLS Linked Service created: AzureDataLakeStorage_LinkedService")
    except Exception as e:
        print(f"   [ERROR] Error creating ADLS linked service: {e}")
        return False
    
    # Step 2: Create SQL Database Linked Service
    print("\nStep 2: Creating Azure SQL Database Linked Service...")
    try:
        sql_linked_service = LinkedServiceResource(
            properties=AzureSqlDatabaseLinkedService(
                connection_string=f"Server=tcp:{sql_server},1433;Database={sql_database};User ID={sql_username};Password={sql_password};Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"
            )
        )
        adf_client.linked_services.create_or_update(
            resource_group,
            adf_name,
            "AzureSqlDatabase_LinkedService",
            sql_linked_service
        )
        print("   [OK] SQL Database Linked Service created: AzureSqlDatabase_LinkedService")
    except Exception as e:
        print(f"   [ERROR] Error creating SQL linked service: {e}")
        return False
    
    # Step 3: Create Source Dataset (ADLS Parquet) with parameterized file name
    print("\nStep 3: Creating Source Dataset (ADLS Parquet)...")
    try:
        from azure.mgmt.datafactory.models import DatasetFolder, ParquetDataset
        source_dataset = DatasetResource(
            properties=ParquetDataset(
                linked_service_name=LinkedServiceReference(
                    type="LinkedServiceReference",
                    reference_name="AzureDataLakeStorage_LinkedService"
                ),
                location=AzureBlobFSLocation(
                    type="AzureBlobFSLocation",
                    file_system="processed",
                    folder_path="processed-data"
                )
            )
        )
        adf_client.datasets.create_or_update(
            resource_group,
            adf_name,
            "SourceDataset_ADLS_Parquet",
            source_dataset
        )
        print("   [OK] Source Dataset created: SourceDataset_ADLS_Parquet")
    except Exception as e:
        print(f"   [ERROR] Error creating source dataset: {e}")
        return False
    
    # Step 4: Create Sink Dataset (SQL Table)
    print("\nStep 4: Creating Sink Dataset (SQL Table)...")
    try:
        sink_dataset = DatasetResource(
            properties=AzureSqlTableDataset(
                linked_service_name=LinkedServiceReference(
                    type="LinkedServiceReference",
                    reference_name="AzureSqlDatabase_LinkedService"
                ),
                table_name="nyc_311_requests"
            )
        )
        adf_client.datasets.create_or_update(
            resource_group,
            adf_name,
            "SinkDataset_SQL_Table",
            sink_dataset
        )
        print("   [OK] Sink Dataset created: SinkDataset_SQL_Table")
    except Exception as e:
        print(f"   [ERROR] Error creating sink dataset: {e}")
        return False
    
    # Step 5: Create Copy Activity pipeline (robust, parameterized by fileName)
    print("\nStep 5: Creating Copy Activity pipeline (ADLS Parquet -> Azure SQL)...")
    try:
        # Define copy source with wildcard file name driven by pipeline parameter 'fileName'
        copy_source = ParquetSource(
            store_settings=AzureBlobFSReadSettings(
                wildcard_file_name='@{pipeline().parameters.fileName}'
            )
        )

        # Define SQL sink - Use TRUNCATE mode since Python handles deduplication
        # Single master file approach: truncate and reload entire dataset each time
        sql_sink = SqlSink(
            write_behavior="insert",
            sql_writer_stored_procedure_name=None,
            sql_writer_table_type=None,
            pre_copy_script="TRUNCATE TABLE nyc_311_requests"  # Clear table before insert
        )

        # Build Copy Activity
        copy_activity = CopyActivity(
            name="CopyParquetToSql",
            inputs=[DatasetReference(type="DatasetReference", reference_name="SourceDataset_ADLS_Parquet")],
            outputs=[DatasetReference(type="DatasetReference", reference_name="SinkDataset_SQL_Table")],
            source=copy_source,
            sink=sql_sink
        )

        # Add parameters for fileName (and optional timestamp for logging)
        pipeline = PipelineResource(
            activities=[copy_activity],
            parameters={
                "fileName": ParameterSpecification(type="String"),
                "timestamp": ParameterSpecification(type="String")
            }
        )

        # Create/Update pipeline
        adf_client.pipelines.create_or_update(
            resource_group,
            adf_name,
            "CopyProcessedDataToSQL",
            pipeline
        )

        print("   [OK] Copy Activity pipeline created/updated successfully: CopyProcessedDataToSQL")
        print("   [OK] Using TRUNCATE mode - single master file contains all deduplicated data")
    except Exception as e:
        print(f"   [ERROR] Error creating Copy Activity pipeline: {e}")
        return False
    
    # Step 6 (optional): Also create a Mapping Data Flow pipeline with corrected script
    print("\nStep 6: Creating optional Mapping Data Flow pipeline with corrected script...")
    try:
        script_lines = [
            "source(allowSchemaDrift: true, validateSchema: false, ignoreNoFilesFound: false, dataset: 'SourceDataset_ADLS_Parquet') ~> Source_ADLS_Parquet",
            "Source_ADLS_Parquet derive(\n"
            "  created_date = iif(isNull(toLong(created_date)), toTimestamp(created_date), toTimestamp(toLong(created_date) / 1000000000)),\n"
            "  closed_date = iif(isNull(toLong(closed_date)), toTimestamp(closed_date), toTimestamp(toLong(closed_date) / 1000000000)),\n"
            "  processed_at = iif(isNull(toLong(processed_at)), toTimestamp(processed_at), toTimestamp(toLong(processed_at) / 1000000000))\n"
            ") ~> ConvertDates",
            "ConvertDates sink(allowSchemaDrift: true, validateSchema: false, deletable: false, insertable: true, updateable: false, upsertable: false, dataset: 'SinkDataset_SQL_Table') ~> Sink_SQL_Table"
        ]

        data_flow = DataFlowResource(
            properties=MappingDataFlow(
                script='\n'.join(script_lines)
            )
        )

        adf_client.data_flows.create_or_update(
            resource_group,
            adf_name,
            "DF_ConvertAndLoad_ParquetToSQL",
            data_flow
        )

        dataflow_activity = ExecuteDataFlowActivity(
            name="TransformAndLoadToSQL",
            data_flow=DataFlowReference(type="DataFlowReference", reference_name="DF_ConvertAndLoad_ParquetToSQL")
        )

        df_pipeline = PipelineResource(
            activities=[dataflow_activity]
        )

        adf_client.pipelines.create_or_update(
            resource_group,
            adf_name,
            "CopyProcessedDataToSQL_DataFlow",
            df_pipeline
        )

        print("   [OK] Data Flow pipeline created/updated: CopyProcessedDataToSQL_DataFlow")
    except Exception as e:
        print(f"   [WARN] Skipped Data Flow pipeline due to error: {e}")

    # Summary
    print("\n" + "="*60)
    print("  ADF PIPELINE SETUP COMPLETED")
    print("="*60)
    print("\nCreated Resources:")
    print("  - Linked Services:")
    print("    - AzureDataLakeStorage_LinkedService")
    print("    - AzureSqlDatabase_LinkedService")
    print("  - Datasets:")
    print("    - SourceDataset_ADLS_Parquet (processed container)")
    print("    - SinkDataset_SQL_Table (nyc_311_requests)")
    print("  - Pipeline:")
    print("    - CopyProcessedDataToSQL")
    print("\nNext Steps:")
    print("  1. Create SQL table schema (nyc_311_requests)")
    print("  2. Test pipeline in Azure Portal")
    print("  3. Integrate with Airflow DAG")
    print("  4. When triggering, pass parameter fileName with the exact Parquet file to load")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = create_adf_pipeline()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Pipeline creation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
