# Create Service Principal for ETL Pipeline
# This Service Principal will survive infrastructure destroy/recreate cycles

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SERVICE PRINCIPAL CREATION" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

# Add Azure CLI to PATH
$env:PATH += ";C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"

# Check if az is available
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Azure CLI not found!" -ForegroundColor Red
    Write-Host "Please ensure Azure CLI is installed." -ForegroundColor Yellow
    exit 1
}

Write-Host "Step 1: Creating Service Principal..." -ForegroundColor Yellow
Write-Host "This will have access to the entire resource group" -ForegroundColor White
Write-Host ""

# Create Service Principal with Contributor role on resource group
$sp = az ad sp create-for-rbac --name "urban-cities-etl-sp" `
    --role "Contributor" `
    --scopes "/subscriptions/12f0f306-0cdf-41a6-9028-a7757690a1e2/resourceGroups/urban-cities-rg" `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create Service Principal" -ForegroundColor Red
    Write-Host "You may need to run: az login" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Service Principal created successfully!" -ForegroundColor Green
Write-Host ""

# Display the credentials
Write-Host "Service Principal Details:" -ForegroundColor Yellow
Write-Host "  App ID (Client ID): " -NoNewline -ForegroundColor White
Write-Host $sp.appId -ForegroundColor Cyan
Write-Host "  Password (Client Secret): " -NoNewline -ForegroundColor White
Write-Host $sp.password -ForegroundColor Cyan
Write-Host "  Tenant ID: " -NoNewline -ForegroundColor White
Write-Host $sp.tenant -ForegroundColor Cyan
Write-Host ""

# Grant Storage Blob Data Owner role
Write-Host "Step 2: Granting Storage Blob Data Owner role..." -ForegroundColor Yellow
az role assignment create `
    --assignee $sp.appId `
    --role "Storage Blob Data Owner" `
    --scope "/subscriptions/12f0f306-0cdf-41a6-9028-a7757690a1e2/resourceGroups/urban-cities-rg/providers/Microsoft.Storage/storageAccounts/urbancitiesadls2025" `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Storage Blob Data Owner role assigned!" -ForegroundColor Green
} else {
    Write-Host "⚠ Warning: Storage role assignment may have failed" -ForegroundColor Yellow
}
Write-Host ""

# Update .env file
Write-Host "Step 3: Updating .env file..." -ForegroundColor Yellow

$envFile = Join-Path $PSScriptRoot ".env"
$content = Get-Content $envFile -Raw

# Remove ADLS_ACCOUNT_KEY line and add Service Principal credentials
$content = $content -replace "ADLS_ACCOUNT_KEY=.*`r?`n", ""

# Check if AZURE_CLIENT_ID exists
if ($content -notmatch "AZURE_CLIENT_ID=") {
    # Add Service Principal credentials after AZURE_TENANT_ID
    $content = $content -replace "(AZURE_TENANT_ID=.*)", "`$1`r`n`r`n# Service Principal (survives infrastructure changes)`r`nAZURE_CLIENT_ID=$($sp.appId)`r`nAZURE_CLIENT_SECRET=$($sp.password)"
} else {
    # Update existing values
    $content = $content -replace "AZURE_CLIENT_ID=.*", "AZURE_CLIENT_ID=$($sp.appId)"
    $content = $content -replace "AZURE_CLIENT_SECRET=.*", "AZURE_CLIENT_SECRET=$($sp.password)"
}

# Save updated .env file
$content | Set-Content $envFile -NoNewline

Write-Host "✓ .env file updated!" -ForegroundColor Green
Write-Host "  - Removed ADLS_ACCOUNT_KEY" -ForegroundColor White
Write-Host "  - Added AZURE_CLIENT_ID" -ForegroundColor White
Write-Host "  - Added AZURE_CLIENT_SECRET" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✓ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your ETL pipeline will now survive infrastructure changes!" -ForegroundColor Green
Write-Host "The Service Principal credentials remain valid even after" -ForegroundColor White
Write-Host "destroying and recreating the infrastructure." -ForegroundColor White
Write-Host ""
Write-Host "Next: Run the test again to verify:" -ForegroundColor Yellow
Write-Host "  python test_azure_connection.py" -ForegroundColor Cyan
Write-Host ""
