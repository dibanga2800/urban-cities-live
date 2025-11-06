FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY Extraction.py ./
COPY Transformation.py ./
COPY Loading.py ./
COPY dag_script.py ./dags/
COPY dags/ ./dags/

# Set environment variables
ENV PYTHONPATH=/app
ENV AIRFLOW_HOME=/app/airflow

# Create airflow directory
RUN mkdir -p /app/airflow

# Expose Airflow webserver port
EXPOSE 8080

# Start Airflow services
CMD ["bash", "-c", "airflow scheduler & airflow webserver --port 8080"]
