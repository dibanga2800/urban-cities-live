# setup_airflow.ps1 - Complete Airflow Setup Script for Windows

Write-Host "🚀 Setting up Apache Airflow with Docker for NYC 311 ETL Pipeline" -ForegroundColor Green

# Step 1: Generate Fernet Key
Write-Host "📝 Generating Fernet Key..." -ForegroundColor Yellow
$FernetKey = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
Write-Host "Generated Fernet Key: $FernetKey" -ForegroundColor Cyan

# Step 2: Update .env file with the Fernet key
Write-Host "🔧 Updating environment configuration..." -ForegroundColor Yellow
(Get-Content .env) -replace 'your_fernet_key_here', $FernetKey | Set-Content .env
Write-Host "✅ Environment file updated" -ForegroundColor Green

# Step 3: Build Docker images
Write-Host "🏗️ Building Docker images..." -ForegroundColor Yellow
docker-compose build

# Step 4: Initialize Airflow database
Write-Host "💾 Initializing Airflow database..." -ForegroundColor Yellow
docker-compose run --rm airflow-webserver airflow db init

# Step 5: Create Airflow admin user
Write-Host "👤 Creating Airflow admin user..." -ForegroundColor Yellow
docker-compose run --rm airflow-webserver airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin

# Step 6: Start services
Write-Host "🚀 Starting Airflow services..." -ForegroundColor Yellow
docker-compose up -d

# Step 7: Wait for services to be ready
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Step 8: Show status
Write-Host "📊 Service Status:" -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "🌐 Airflow Web UI: http://localhost:8080" -ForegroundColor Cyan
Write-Host "👤 Username: admin" -ForegroundColor Cyan
Write-Host "🔑 Password: admin" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Useful Commands:" -ForegroundColor Yellow
Write-Host "  - View logs: docker-compose logs" -ForegroundColor Gray
Write-Host "  - Stop services: docker-compose down" -ForegroundColor Gray
Write-Host "  - Restart services: docker-compose restart" -ForegroundColor Gray
Write-Host "  - View DAGs: docker-compose exec airflow-webserver airflow dags list" -ForegroundColor Gray