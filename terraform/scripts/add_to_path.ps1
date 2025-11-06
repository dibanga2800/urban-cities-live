# Script to add Terraform to PATH
# This adds the directory to your User PATH (no admin required)

# First, let's check if terraform.exe exists in common locations
$possiblePaths = @(
    "C:\Users\David Ibanga\terraform",
    "C:\terraform",
    "C:\ProgramData\chocolatey\bin",
    "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
)

Write-Host "Searching for terraform.exe..." -ForegroundColor Cyan
Write-Host ""

$terraformPath = $null
foreach ($path in $possiblePaths) {
    if (Test-Path "$path\terraform.exe") {
        $terraformPath = $path
        Write-Host "[FOUND] terraform.exe at: $path" -ForegroundColor Green
        break
    }
}

if (-not $terraformPath) {
    Write-Host "[NOT FOUND] terraform.exe not found in common locations" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please enter the full path to the folder containing terraform.exe" -ForegroundColor Yellow
    Write-Host "Example: C:\Users\David Ibanga\terraform" -ForegroundColor Gray
    $terraformPath = Read-Host "Enter path"
    
    if (-not (Test-Path "$terraformPath\terraform.exe")) {
        Write-Host "[ERROR] terraform.exe not found at $terraformPath" -ForegroundColor Red
        Write-Host "Please download Terraform first from: https://www.terraform.io/downloads" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Adding to PATH: $terraformPath" -ForegroundColor Cyan

# Get current User PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Check if already in PATH
if ($currentPath -split ";" -contains $terraformPath) {
    Write-Host "[INFO] This path is already in your PATH variable" -ForegroundColor Yellow
} else {
    # Add to PATH
    $newPath = $currentPath + ";" + $terraformPath
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "[SUCCESS] Added to PATH successfully!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Updating current session PATH..." -ForegroundColor Cyan
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host ""
Write-Host "Testing terraform command..." -ForegroundColor Cyan
try {
    $version = & "$terraformPath\terraform.exe" version 2>&1
    Write-Host "[SUCCESS] Terraform is now accessible!" -ForegroundColor Green
    Write-Host $version -ForegroundColor White
} catch {
    Write-Host "[INFO] Close this PowerShell window and open a new one for PATH changes to take effect" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "IMPORTANT: Close ALL PowerShell windows and open a new one to use 'terraform' command" -ForegroundColor Cyan
Write-Host ""
