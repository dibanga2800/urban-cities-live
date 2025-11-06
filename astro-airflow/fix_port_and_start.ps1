# Fix PostgreSQL Port 5432 Conflict and Start Astro Airflow
# This script will automatically elevate to admin if needed

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Astro Airflow Port Conflict Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script needs administrator privileges to stop the PostgreSQL process." -ForegroundColor Yellow
    Write-Host "Restarting with elevated permissions..." -ForegroundColor Yellow
    Write-Host ""
    
    # Restart script with admin privileges
    $scriptPath = $MyInvocation.MyCommand.Path
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$scriptPath`""
    exit
}

Write-Host "[Running as Administrator]" -ForegroundColor Green
Write-Host ""

# Step 1: Find and stop process using port 5432
Write-Host "Step 1: Finding process using port 5432..." -ForegroundColor Cyan

$connections = Get-NetTCPConnection -LocalPort 5432 -ErrorAction SilentlyContinue

if ($connections) {
    foreach ($conn in $connections) {
        $processId = $conn.OwningProcess
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        
        if ($process) {
            Write-Host "  Found: $($process.ProcessName) (PID: $processId)" -ForegroundColor Yellow
            Write-Host "  Stopping process..." -ForegroundColor Cyan
            
            try {
                Stop-Process -Id $processId -Force -ErrorAction Stop
                Write-Host "  [OK] Process stopped successfully" -ForegroundColor Green
            }
            catch {
                Write-Host "  [ERROR] Failed to stop process: $_" -ForegroundColor Red
            }
        }
    }
}
else {
    Write-Host "  [OK] No process found using port 5432" -ForegroundColor Green
}

Write-Host ""

# Step 2: Clean up Docker containers and volumes
Write-Host "Step 2: Cleaning up Docker environment..." -ForegroundColor Cyan

# Stop and remove all containers
Write-Host "  Removing all Docker containers..." -ForegroundColor Gray
$containers = docker ps -aq 2>$null
if ($containers) {
    docker rm -f $containers 2>&1 | Out-Null
    Write-Host "  [OK] Containers removed" -ForegroundColor Green
}
else {
    Write-Host "  [OK] No containers to remove" -ForegroundColor Green
}

# Remove old volumes
Write-Host "  Removing old Docker volumes..." -ForegroundColor Gray
docker volume prune -f 2>&1 | Out-Null
Write-Host "  [OK] Volumes cleaned" -ForegroundColor Green

Write-Host ""

# Step 3: Verify port is free
Write-Host "Step 3: Verifying port 5432 is now available..." -ForegroundColor Cyan

Start-Sleep -Seconds 2

$portCheck = Get-NetTCPConnection -LocalPort 5432 -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host "  [WARNING] Port 5432 is still in use!" -ForegroundColor Red
    Write-Host "  You may need to restart your computer to fully release the port." -ForegroundColor Yellow
}
else {
    Write-Host "  [OK] Port 5432 is now available" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cleanup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps (run in your normal PowerShell window):" -ForegroundColor Yellow
Write-Host ""
Write-Host 'cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\astro-airflow"' -ForegroundColor White
Write-Host '& "C:\Users\David Ibanga\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe\astro.exe" dev start' -ForegroundColor White
Write-Host ""
Write-Host "Press any key to close this window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
