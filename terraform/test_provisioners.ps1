<#
Simple validation script for Terraform provisioner target scripts.
All color flags removed to avoid parsing issues across environments.
#>
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'

Write-Host ''
Write-Host '==== TESTING TERRAFORM PROVISIONERS ===='
Write-Host ''

# SQL Table
Write-Host 'Test 1: SQL Table Creation'
Write-Host 'Running: python scripts/sql/create_sql_table.py'
python "$PSScriptRoot\..\scripts\sql\create_sql_table.py" | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host 'SQL table creation script failed with exit code' $LASTEXITCODE
    exit $LASTEXITCODE
} else {
    Write-Host 'SQL table creation script exited successfully'
}

Write-Host ''
# ADF Pipeline
Write-Host 'Test 2: ADF Pipeline Creation'
Write-Host 'Running: python scripts/adf/create_adf_pipeline.py'
python "$PSScriptRoot\..\scripts\adf\create_adf_pipeline.py" | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host 'ADF pipeline creation script failed with exit code' $LASTEXITCODE
    exit $LASTEXITCODE
} else {
    Write-Host 'ADF pipeline creation script exited successfully'
}

Write-Host ''
Write-Host '==== ALL TESTS PASSED ===='
Write-Host 'Terraform provisioners should succeed on apply.'
Write-Host 'Next: terraform destroy -auto-approve ; terraform apply -auto-approve'
Write-Host ''
