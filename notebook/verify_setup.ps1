# verify_setup.ps1 - Verify Docker and Prerequisites

Write-Host "🔍 Verifying Docker Setup for Airflow..." -ForegroundColor Green
Write-Host ""

# Check Docker installation
Write-Host "1. Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found in PATH. Please:" -ForegroundColor Red
    Write-Host "   - Ensure Docker Desktop is running" -ForegroundColor Yellow
    Write-Host "   - Restart PowerShell as Administrator" -ForegroundColor Yellow
    Write-Host "   - Check Docker Desktop system tray icon" -ForegroundColor Yellow
    exit 1
}

# Check Docker Compose
Write-Host "2. Checking Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose found: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose not found" -ForegroundColor Red
    exit 1
}

# Check if Docker daemon is running
Write-Host "3. Checking Docker daemon..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "✅ Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker daemon not running. Please start Docker Desktop" -ForegroundColor Red
    exit 1
}

# Check required files
Write-Host "4. Checking required files..." -ForegroundColor Yellow
$requiredFiles = @(
    "docker-compose.yml",
    "Dockerfile", 
    ".env",
    "Extraction.py",
    "Transformation.py",
    "Loading.py",
    "requirements.txt"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ Found: $file" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing: $file" -ForegroundColor Red
    }
}

# Check directories
Write-Host "5. Checking directories..." -ForegroundColor Yellow
$requiredDirs = @("dags", "logs", "plugins", "data")

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "✅ Directory exists: $dir" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Creating directory: $dir" -ForegroundColor Yellow
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "✅ Created: $dir" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "🎯 System Check Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. If all checks passed, run: .\setup_airflow.ps1" -ForegroundColor White
Write-Host "2. If Docker failed, start Docker Desktop and try again" -ForegroundColor White
Write-Host "3. If files missing, check your project structure" -ForegroundColor White
Write-Host ""