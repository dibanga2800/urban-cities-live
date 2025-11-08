# Quick Start Script for Terraform Azure Infrastructure
# This script guides you through the infrastructure deployment process

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Urban Cities Live Service - Terraform Quick Start        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$terraformDir = $PSScriptRoot
Set-Location $terraformDir

# Function to check prerequisites
function Test-Prerequisites {
    Write-Host "Checking prerequisites..." -ForegroundColor Yellow
    Write-Host ""
    
    $allGood = $true
    
    # Check Terraform
    try {
        $tfVersion = terraform version 2>&1
        Write-Host "✓ Terraform: " -ForegroundColor Green -NoNewline
        Write-Host ($tfVersion | Select-Object -First 1)
    } catch {
        Write-Host "✗ Terraform not found" -ForegroundColor Red
        Write-Host "  Run setup.ps1 to install Terraform" -ForegroundColor Yellow
        $allGood = $false
    }
    
    # Check Azure CLI
    try {
        $azVersion = (az version | ConvertFrom-Json).'azure-cli'
        Write-Host "✓ Azure CLI: " -ForegroundColor Green -NoNewline
        Write-Host $azVersion
    } catch {
        Write-Host "✗ Azure CLI not found" -ForegroundColor Red
        Write-Host "  Run setup.ps1 to install Azure CLI" -ForegroundColor Yellow
        $allGood = $false
    }
    
    # Check Azure login
    try {
        $account = az account show 2>&1 | ConvertFrom-Json
        Write-Host "✓ Azure: Logged in as " -ForegroundColor Green -NoNewline
        Write-Host $account.user.name
        Write-Host "  Subscription: " -ForegroundColor Gray -NoNewline
        Write-Host $account.name
    } catch {
        Write-Host "✗ Not logged into Azure" -ForegroundColor Red
        Write-Host "  Run 'az login' to authenticate" -ForegroundColor Yellow
        $allGood = $false
    }
    
    # Check terraform.tfvars
    if (Test-Path "terraform.tfvars") {
        Write-Host "✓ terraform.tfvars exists" -ForegroundColor Green
    } else {
        Write-Host "✗ terraform.tfvars not found" -ForegroundColor Red
        Write-Host "  Copy terraform.tfvars.example to terraform.tfvars and edit" -ForegroundColor Yellow
        $allGood = $false
    }
    
    Write-Host ""
    return $allGood
}

# Check prerequisites
if (-not (Test-Prerequisites)) {
    Write-Host "Please resolve the issues above before continuing." -ForegroundColor Red
    Write-Host ""
    exit 1
}

# Main menu
while ($true) {
    Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "What would you like to do?" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Initialize Terraform" -ForegroundColor White
    Write-Host "2. Validate configuration" -ForegroundColor White
    Write-Host "3. Plan infrastructure (dry run)" -ForegroundColor White
    Write-Host "4. Apply infrastructure (create resources)" -ForegroundColor White
    Write-Host "5. Show outputs" -ForegroundColor White
    Write-Host "6. Destroy infrastructure" -ForegroundColor White
    Write-Host "7. Format Terraform files" -ForegroundColor White
    Write-Host "8. Exit" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "Enter your choice (1-8)"
    Write-Host ""
    
    switch ($choice) {
        "1" {
            Write-Host "Initializing Terraform..." -ForegroundColor Yellow
            terraform init
            Write-Host ""
        }
        "2" {
            Write-Host "Validating configuration..." -ForegroundColor Yellow
            terraform validate
            Write-Host ""
        }
        "3" {
            Write-Host "Planning infrastructure changes..." -ForegroundColor Yellow
            Write-Host ""
            terraform plan
            Write-Host ""
        }
        "4" {
            Write-Host "WARNING: This will create real Azure resources and may incur costs!" -ForegroundColor Yellow
            Write-Host ""
            $confirm = Read-Host "Are you sure you want to apply? (type 'yes' to confirm)"
            if ($confirm -eq "yes") {
                Write-Host ""
                Write-Host "Applying infrastructure changes..." -ForegroundColor Yellow
                terraform apply
                Write-Host ""
                Write-Host "✓ Infrastructure applied successfully!" -ForegroundColor Green
                Write-Host ""
                # Post-apply: Create/Update ADF pipeline to prevent Airflow trigger errors
                try {
                    Write-Host "Creating/Updating ADF pipeline (post-apply step)..." -ForegroundColor Yellow
                    $repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
                    $adfScript = Join-Path $repoRoot "scripts/adf/create_adf_pipeline.py"
                    if (Test-Path $adfScript) {
                        # Prefer python from PATH
                        $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
                        if (-not $pythonCmd) {
                            Write-Host "Python not found in PATH. Attempting 'py' launcher..." -ForegroundColor Yellow
                            py -3 $adfScript
                        } else {
                            python $adfScript
                        }
                        Write-Host "✓ ADF pipeline ensured (CopyProcessedDataToSQL)" -ForegroundColor Green
                    } else {
                        Write-Host "⚠ ADF creation script not found: $adfScript" -ForegroundColor Yellow
                    }
                } catch {
                    Write-Host "✗ Failed to create ADF pipeline automatically. Run scripts/adf/create_adf_pipeline.py manually." -ForegroundColor Red
                }
                Write-Host "Run option 5 to see the outputs (connection strings, etc.)" -ForegroundColor Cyan
            } else {
                Write-Host "Cancelled." -ForegroundColor Yellow
            }
            Write-Host ""
        }
        "5" {
            Write-Host "Terraform Outputs:" -ForegroundColor Yellow
            Write-Host ""
            terraform output
            Write-Host ""
            Write-Host "To see sensitive values, run:" -ForegroundColor Cyan
            Write-Host "  terraform output -json" -ForegroundColor White
            Write-Host "  terraform output storage_account_primary_access_key" -ForegroundColor White
            Write-Host ""
        }
        "6" {
            Write-Host "WARNING: This will DELETE all Azure resources managed by Terraform!" -ForegroundColor Red
            Write-Host ""
            $confirm = Read-Host "Are you sure you want to destroy? (type 'yes' to confirm)"
            if ($confirm -eq "yes") {
                Write-Host ""
                Write-Host "Destroying infrastructure..." -ForegroundColor Yellow
                terraform destroy
                Write-Host ""
            } else {
                Write-Host "Cancelled." -ForegroundColor Yellow
            }
            Write-Host ""
        }
        "7" {
            Write-Host "Formatting Terraform files..." -ForegroundColor Yellow
            terraform fmt -recursive
            Write-Host "✓ Done!" -ForegroundColor Green
            Write-Host ""
        }
        "8" {
            Write-Host "Goodbye!" -ForegroundColor Cyan
            exit 0
        }
        default {
            Write-Host "Invalid choice. Please enter 1-8." -ForegroundColor Red
            Write-Host ""
        }
    }
    
    Read-Host "Press Enter to continue"
    Write-Host ""
}
