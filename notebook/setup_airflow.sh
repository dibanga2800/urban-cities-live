#!/bin/bash
# setup_airflow.sh - Complete Airflow Setup Script

echo "🚀 Setting up Apache Airflow with Docker for NYC 311 ETL Pipeline"

# Step 1: Generate Fernet Key
echo "📝 Generating Fernet Key..."
FERNET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
echo "Generated Fernet Key: $FERNET_KEY"

# Step 2: Update .env file with the Fernet key
echo "🔧 Updating environment configuration..."
sed -i "s/your_fernet_key_here/$FERNET_KEY/" .env
echo "✅ Environment file updated"

# Step 3: Build Docker images
echo "🏗️ Building Docker images..."
docker-compose build

# Step 4: Initialize Airflow database
echo "💾 Initializing Airflow database..."
docker-compose run --rm airflow-webserver airflow db init

# Step 5: Create Airflow admin user
echo "👤 Creating Airflow admin user..."
docker-compose run --rm airflow-webserver airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin

# Step 6: Start services
echo "🚀 Starting Airflow services..."
docker-compose up -d

# Step 7: Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Step 8: Show status
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ Setup Complete!"
echo "🌐 Airflow Web UI: http://localhost:8080"
echo "👤 Username: admin"
echo "🔑 Password: admin"
echo ""
echo "📋 Useful Commands:"
echo "  - View logs: docker-compose logs"
echo "  - Stop services: docker-compose down"
echo "  - Restart services: docker-compose restart"
echo "  - View DAGs: docker-compose exec airflow-webserver airflow dags list"