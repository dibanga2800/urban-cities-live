# Regenerate Service Principal Client Secret
# This script creates a new client secret for the existing service principal

Write-Host "Regenerating client secret for service principal..." -ForegroundColor Cyan

# Service Principal details
$appId = "27b470a2-fa5d-458a-85d5-e639c0791f23"
$displayName = "urban-cities-etl-sp"

# Check if logged in to Azure
$context = Get-AzContext -ErrorAction SilentlyContinue
if (-not $context) {
    Write-Host "Not logged in to Azure. Running az login..." -ForegroundColor Yellow
    az login
}

# Create new client secret (valid for 1 year)
Write-Host "`nCreating new client secret..." -ForegroundColor Cyan
$secretName = "urban-cities-secret-$(Get-Date -Format 'yyyyMMdd')"
$endDate = (Get-Date).AddYears(1).ToString("yyyy-MM-dd")

$result = az ad app credential reset `
    --id $appId `
    --append `
    --display-name $secretName `
    --end-date $endDate `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ New client secret created successfully!" -ForegroundColor Green
    Write-Host "`n⚠️  SAVE THIS SECRET NOW - IT WON'T BE SHOWN AGAIN!" -ForegroundColor Yellow
    Write-Host "`nService Principal Details:" -ForegroundColor Cyan
    Write-Host "=========================" -ForegroundColor Cyan
    Write-Host "App ID (Client ID): $appId"
    Write-Host "Tenant ID: $($result.tenant)"
    Write-Host "Client Secret: $($result.password)" -ForegroundColor Yellow
    Write-Host "Expires: $endDate"
    Write-Host "=========================`n" -ForegroundColor Cyan
    
    # Update .env file
    $envPath = ".env"
    Write-Host "Updating $envPath file..." -ForegroundColor Cyan
    
    if (Test-Path $envPath) {
        $envContent = Get-Content $envPath -Raw
        
        # Update AZURE_CLIENT_ID
        if ($envContent -match 'AZURE_CLIENT_ID=.*') {
            $envContent = $envContent -replace 'AZURE_CLIENT_ID=.*', "AZURE_CLIENT_ID=$appId"
        } else {
            $envContent += "`nAZURE_CLIENT_ID=$appId"
        }
        
        # Update AZURE_CLIENT_SECRET
        if ($envContent -match 'AZURE_CLIENT_SECRET=.*') {
            $envContent = $envContent -replace 'AZURE_CLIENT_SECRET=.*', "AZURE_CLIENT_SECRET=$($result.password)"
        } else {
            $envContent += "`nAZURE_CLIENT_SECRET=$($result.password)"
        }
        
        # Update AZURE_TENANT_ID
        if ($envContent -match 'AZURE_TENANT_ID=.*') {
            $envContent = $envContent -replace 'AZURE_TENANT_ID=.*', "AZURE_TENANT_ID=$($result.tenant)"
        } else {
            $envContent += "`nAZURE_TENANT_ID=$($result.tenant)"
        }
        
        $envContent | Set-Content $envPath -NoNewline
        Write-Host "✅ .env file updated successfully!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  .env file not found. Please create it manually." -ForegroundColor Yellow
    }
    
    Write-Host "`nYou can now use the updated credentials in your applications." -ForegroundColor Green
    
} else {
    Write-Host "`n❌ Failed to create new client secret." -ForegroundColor Red
    Write-Host "Please check your Azure permissions and try again." -ForegroundColor Yellow
}
