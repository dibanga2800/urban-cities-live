# NYC 311 Near Real-Time ETL Pipeline

## Overview
Production-ready ETL pipeline for NYC 311 service requests with:
- Incremental loading - Only processes new/updated records
- Apache Airflow orchestration - Automated scheduling and monitoring
- Modular architecture - Clean separation of Extract, Transform, Load
- Azure Data Lake storage - Scalable cloud data storage
- Docker deployment - Containerized for easy deployment

## Architecture

NYC 311 API -> Data Extractor -> Data Transformer -> Data Loader -> Azure Data Lake
                               (Orchestrated by Apache Airflow)

## Features
- Incremental Processing: State management tracks last processed timestamp
- Near Real-Time: Runs every 15 minutes
- Error Handling: 3 retries with exponential backoff
- Data Quality: Validation and cleaning
- Monitoring: Airflow UI for pipeline monitoring
- Scalable: Containerized and cloud-ready

## Quick Start

1. Setup Environment
cp .env.example .env
# Edit .env with your configuration

2. Deploy with Docker
docker-compose up -d

3. Access Airflow UI
Open http://localhost:8080
- Username: admin
- Password: admin

4. Enable DAG
In Airflow UI, enable the nyc_311_incremental_etl DAG

## Configuration

Required Environment Variables:
- NYC_311_API_URL: NYC 311 API endpoint
- AZURE_STORAGE_ACCOUNT_NAME: Azure storage account
- AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID: Azure auth

Optional Configuration:
- BATCH_SIZE: API batch size (default: 1000)
- AZURE_CONTAINER_NAME: Storage container (default: nyc-311-data)
- AZURE_DIRECTORY_NAME: Storage directory (default: incremental)

## Module Structure

nyc_311_etl/
├── config.py          # Configuration management
├── extractor.py       # Data extraction from API
├── transformer.py     # Data cleaning and transformation
├── loader.py          # Loading to Azure Data Lake
├── state_manager.py   # Incremental state tracking
└── orchestrator.py    # ETL workflow coordination

## Monitoring & Operations

Pipeline Metrics:
- Records processed per run
- Processing time
- Data quality scores
- Error rates

Airflow Monitoring:
- DAG run history
- Task success/failure rates
- SLA monitoring
- Email alerts

## Development

Running Tests:
pytest tests/

Code Quality:
black nyc_311_etl/
flake8 nyc_311_etl/

## Deployment Options

Local Development:
python -m nyc_311_etl.orchestrator

Production (Docker):
docker-compose up -d

Cloud Deployment:
- Azure Container Instances
- Azure Kubernetes Service
- AWS ECS/EKS
- Google Cloud Run
