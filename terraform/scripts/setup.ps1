# PowerShell script to install Terraform and set up Azure authentication
# Run this script as Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Terraform & Azure Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check if running as administrator
if (-not (Test-Administrator)) {
    Write-Host "WARNING: This script should be run as Administrator for best results." -ForegroundColor Yellow
    Write-Host "Some features may not work without admin privileges." -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Do you want to continue anyway? (y/n)"
    if ($continue -ne 'y') {
        exit
    }
}

# Step 1: Check and install Chocolatey
Write-Host "[1/5] Checking Chocolatey installation..." -ForegroundColor Green
try {
    $chocoVersion = choco --version 2>$null
    if ($chocoVersion) {
        Write-Host "[OK] Chocolatey is already installed (version: $chocoVersion)" -ForegroundColor Green
    }
} catch {
    Write-Host "[!] Chocolatey is not installed" -ForegroundColor Yellow
    Write-Host "Installing Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    Write-Host "[OK] Chocolatey installed successfully" -ForegroundColor Green
}

Write-Host ""

# Step 2: Install Terraform
Write-Host "[2/5] Installing Terraform..." -ForegroundColor Green
try {
    $tfVersion = terraform -v 2>$null
    if ($tfVersion) {
        Write-Host "[OK] Terraform is already installed" -ForegroundColor Green
        Write-Host $tfVersion -ForegroundColor Cyan
    }
} catch {
    Write-Host "Installing Terraform via Chocolatey..." -ForegroundColor Yellow
    choco install terraform -y
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    Write-Host "[OK] Terraform installed successfully" -ForegroundColor Green
}

Write-Host ""

# Step 3: Install Azure CLI
Write-Host "[3/5] Checking Azure CLI installation..." -ForegroundColor Green
try {
    $azVersion = az version 2>$null
    if ($azVersion) {
        Write-Host "[OK] Azure CLI is already installed" -ForegroundColor Green
    }
} catch {
    Write-Host "Azure CLI is not installed" -ForegroundColor Yellow
    $installAzCLI = Read-Host "Do you want to install Azure CLI? (y/n)"
    if ($installAzCLI -eq 'y') {
        Write-Host "Installing Azure CLI..." -ForegroundColor Yellow
        choco install azure-cli -y
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        Write-Host "[OK] Azure CLI installed successfully" -ForegroundColor Green
    }
}

Write-Host ""

# Step 4: Azure Authentication
Write-Host "[4/5] Azure Authentication Setup" -ForegroundColor Green
$loginAzure = Read-Host "Do you want to login to Azure now? (y/n)"
if ($loginAzure -eq 'y') {
    Write-Host "Opening Azure login..." -ForegroundColor Yellow
    az login
    
    # Show subscriptions
    Write-Host ""
    Write-Host "Available subscriptions:" -ForegroundColor Cyan
    az account list --output table
    
    Write-Host ""
    $changeSubscription = Read-Host "Do you want to change the active subscription? (y/n)"
    if ($changeSubscription -eq 'y') {
        $subscriptionId = Read-Host "Enter subscription ID"
        az account set --subscription $subscriptionId
        Write-Host "[OK] Subscription changed successfully" -ForegroundColor Green
    }
    
    # Show current account
    Write-Host ""
    Write-Host "Current Azure account:" -ForegroundColor Cyan
    az account show --output table
}

Write-Host ""

# Step 5: Create terraform.tfvars
Write-Host "[5/5] Creating terraform.tfvars file" -ForegroundColor Green
$terraformDir = Join-Path $PSScriptRoot ""
$tfvarsPath = Join-Path $terraformDir "terraform.tfvars"
$tfvarsExamplePath = Join-Path $terraformDir "terraform.tfvars.example"

if (Test-Path $tfvarsPath) {
    Write-Host "[OK] terraform.tfvars already exists" -ForegroundColor Green
} else {
    Write-Host "Creating terraform.tfvars from example..." -ForegroundColor Yellow
    
    if (Test-Path $tfvarsExamplePath) {
        Copy-Item $tfvarsExamplePath $tfvarsPath
        Write-Host "[OK] terraform.tfvars created" -ForegroundColor Green
        Write-Host ""
        Write-Host "IMPORTANT: Edit terraform.tfvars with your specific values!" -ForegroundColor Yellow
        Write-Host "Required changes:" -ForegroundColor Yellow
        Write-Host "  - storage_account_name (must be globally unique)" -ForegroundColor Yellow
        Write-Host "  - postgresql_server_name (must be globally unique)" -ForegroundColor Yellow
        Write-Host "  - postgresql_admin_password (strong password required)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit terraform.tfvars with your configuration" -ForegroundColor White
Write-Host "2. Run: terraform init" -ForegroundColor White
Write-Host "3. Run: terraform plan" -ForegroundColor White
Write-Host "4. Run: terraform apply" -ForegroundColor White
Write-Host ""
Write-Host "For detailed instructions, see README.md" -ForegroundColor Cyan
