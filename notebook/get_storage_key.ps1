# Get Storage Account Key from Azure
# Run this script to get the storage account key and update your .env file

Write-Host "`nGetting storage account key from Azure..." -ForegroundColor Yellow

# Add paths to PATH
$env:PATH += ";C:\terraform"
$env:PATH += ";C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"

# Try Azure CLI first
if (Get-Command az -ErrorAction SilentlyContinue) {
    Write-Host "Using Azure CLI..." -ForegroundColor Green
    $key = az storage account keys list --resource-group urban-cities-rg --account-name urbancitiesadls2025 --query "[0].value" -o tsv
    
    if ($LASTEXITCODE -eq 0 -and $key) {
        Write-Host "`n✓ Storage Account Key Retrieved!" -ForegroundColor Green
        Write-Host "`nCopy this key:" -ForegroundColor Yellow
        Write-Host $key -ForegroundColor White
        
        Write-Host "`nAdd this line to your .env file:" -ForegroundColor Yellow
        Write-Host "ADLS_ACCOUNT_KEY=$key" -ForegroundColor White
        
        # Optionally update .env file automatically
        $updateEnv = Read-Host "`nUpdate .env file automatically? (y/n)"
        if ($updateEnv -eq 'y') {
            $envFile = Join-Path $PSScriptRoot ".env"
            $content = Get-Content $envFile
            
            # Check if ADLS_ACCOUNT_KEY exists
            if ($content -match "^ADLS_ACCOUNT_KEY=") {
                $content = $content -replace "^ADLS_ACCOUNT_KEY=.*", "ADLS_ACCOUNT_KEY=$key"
            } else {
                # Add after ADLS_ACCOUNT_NAME
                $newContent = @()
                foreach ($line in $content) {
                    $newContent += $line
                    if ($line -match "^ADLS_ACCOUNT_NAME=") {
                        $newContent += "ADLS_ACCOUNT_KEY=$key"
                    }
                }
                $content = $newContent
            }
            
            $content | Set-Content $envFile
            Write-Host "✓ .env file updated!" -ForegroundColor Green
        }
    } else {
        Write-Host "✗ Failed to retrieve key using Azure CLI" -ForegroundColor Red
    }
} else {
    Write-Host "✗ Azure CLI not found" -ForegroundColor Red
    Write-Host "`nAlternative: Get the key from Azure Portal:" -ForegroundColor Yellow
    Write-Host "1. Go to https://portal.azure.com" -ForegroundColor White
    Write-Host "2. Navigate to Storage Account 'urbancitiesadls2025'" -ForegroundColor White
    Write-Host "3. Go to 'Access keys' under Security + networking" -ForegroundColor White
    Write-Host "4. Click 'Show' next to key1" -ForegroundColor White
    Write-Host "5. Copy the key value" -ForegroundColor White
    Write-Host "6. Add to .env file: ADLS_ACCOUNT_KEY=<paste_key_here>" -ForegroundColor White
}

Write-Host ""
