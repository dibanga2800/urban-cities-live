# Stop PostgreSQL service that's blocking port 5432
# Run this script as Administrator

Write-Host "Finding process using port 5432..." -ForegroundColor Cyan

$port = 5432
$process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1

if ($process) {
    $processId = $process.OwningProcess
    $processInfo = Get-Process -Id $processId -ErrorAction SilentlyContinue
    
    if ($processInfo) {
        Write-Host "Found process: $($processInfo.ProcessName) (PID: $processId)" -ForegroundColor Yellow
        Write-Host "Stopping process..." -ForegroundColor Cyan
        
        try {
            Stop-Process -Id $processId -Force
            Write-Host "✓ Process stopped successfully!" -ForegroundColor Green
        } catch {
            Write-Host "✗ Failed to stop process. Error: $_" -ForegroundColor Red
            Write-Host ""
            Write-Host "Alternative: Run this command as Administrator:" -ForegroundColor Yellow
            Write-Host "Stop-Process -Id $processId -Force" -ForegroundColor White
        }
    }
} else {
    Write-Host "✓ No process found using port 5432" -ForegroundColor Green
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
