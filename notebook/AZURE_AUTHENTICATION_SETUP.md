# Azure Authentication Setup Guide
## Service Principal Configuration for Infrastructure-Independent Authentication

**Last Updated:** November 4, 2025  
**Project:** NYC 311 ETL Pipeline with Azure Integration

---

## Table of Contents
1. [Overview](#overview)
2. [Why Service Principal?](#why-service-principal)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Setup](#step-by-step-setup)
5. [Testing Authentication](#testing-authentication)
6. [Troubleshooting](#troubleshooting)
7. [Security Best Practices](#security-best-practices)

---

## Overview

This guide documents the complete process of setting up **Service Principal authentication** for the Azure ETL pipeline. Service Principal authentication ensures your pipeline continues to work even after destroying and recreating Azure infrastructure.

### What We Configured:
- ✅ Azure Service Principal with Contributor role
- ✅ Storage Blob Data Owner permissions for ADLS Gen2
- ✅ Infrastructure-independent authentication
- ✅ Production-ready security setup

---

## Why Service Principal?

### The Problem:
When using **Storage Account Keys** for authentication:
- ❌ Keys change every time you destroy and recreate infrastructure
- ❌ Pipeline breaks after infrastructure changes
- ❌ Manual intervention required to update `.env` file
- ❌ Not suitable for production/automation

### The Solution:
Using **Service Principal** authentication:
- ✅ Credentials remain constant across infrastructure rebuilds
- ✅ Pipeline survives destroy/recreate cycles
- ✅ Azure RBAC-based security (recommended by Microsoft)
- ✅ Perfect for CI/CD and production environments

---

## Prerequisites

Before starting, ensure you have:
- ✅ Azure CLI installed
- ✅ Active Azure subscription (with appropriate permissions)
- ✅ Azure infrastructure deployed (Resource Group, ADLS Gen2)
- ✅ Access to create Service Principals (Azure AD permissions)

### Our Infrastructure:
```
Subscription ID: 12f0f306-0cdf-41a6-9028-a7757690a1e2
Tenant ID: edc41ca9-a02a-4623-97cb-2a58f19e3c46
Resource Group: urban-cities-rg
Storage Account: urbancitiesadls2025
Region: West Europe
```

---

## Step-by-Step Setup

### Step 1: Add Azure CLI to PATH

**Windows (PowerShell):**
```powershell
$env:PATH += ';C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin'
```

**Linux/macOS:**
```bash
# Azure CLI is usually in PATH by default
# If not, add: export PATH=$PATH:/usr/local/bin
```

---

### Step 2: Login to Azure

```bash
az login --tenant edc41ca9-a02a-4623-97cb-2a58f19e3c46
```

**What happens:**
- Browser opens for authentication
- Login with your Azure credentials
- Terminal confirms successful authentication

---

### Step 3: Create Service Principal

**Command (single line - copy this):**
```bash
az ad sp create-for-rbac --name 'urban-cities-etl-sp' --role 'Contributor' --scopes '/subscriptions/12f0f306-0cdf-41a6-9028-a7757690a1e2/resourceGroups/urban-cities-rg'
```

**Multi-line format (bash/Linux):**
```bash
az ad sp create-for-rbac \
  --name 'urban-cities-etl-sp' \
  --role 'Contributor' \
  --scopes '/subscriptions/12f0f306-0cdf-41a6-9028-a7757690a1e2/resourceGroups/urban-cities-rg'
```

**Expected Output:**
```json
{
  "appId": "27b470a2-fa5d-458a-85d5-e639c0791f23",
  "displayName": "urban-cities-etl-sp",
  "password": "YOUR_CLIENT_SECRET_HERE",
  "tenant": "edc41ca9-a02a-4623-97cb-2a58f19e3c46"
}
```

**⚠️ IMPORTANT:** Save this output immediately! The password is only shown once.

**What this does:**
- Creates a Service Principal named `urban-cities-etl-sp`
- Grants `Contributor` role on the resource group
- Allows the SP to manage resources in `urban-cities-rg`

---

### Step 4: Grant Storage Permissions

**Command (single line - copy this):**
```bash
az role assignment create --assignee 27b470a2-fa5d-458a-85d5-e639c0791f23 --role 'Storage Blob Data Owner' --scope '/subscriptions/12f0f306-0cdf-41a6-9028-a7757690a1e2/resourceGroups/urban-cities-rg/providers/Microsoft.Storage/storageAccounts/urbancitiesadls2025'
```

**Multi-line format (bash/Linux):**
```bash
az role assignment create \
  --assignee 27b470a2-fa5d-458a-85d5-e639c0791f23 \
  --role 'Storage Blob Data Owner' \
  --scope '/subscriptions/12f0f306-0cdf-41a6-9028-a7757690a1e2/resourceGroups/urban-cities-rg/providers/Microsoft.Storage/storageAccounts/urbancitiesadls2025'
```

**⚠️ Replace `27b470a2-fa5d-458a-85d5-e639c0791f23` with your actual `appId` from Step 3.**

**Expected Output:**
```json
{
  "condition": null,
  "conditionVersion": null,
  "createdOn": "2025-11-04T22:44:08.344370+00:00",
  "principalId": "9306b861-8960-496a-9a0d-3f996df4a7fb",
  "principalType": "ServicePrincipal",
  "roleDefinitionId": ".../roleDefinitions/b7e6dc6d-f1e8-4753-8033-0f276bb0955b",
  "scope": ".../storageAccounts/urbancitiesadls2025",
  "type": "Microsoft.Authorization/roleAssignments"
}
```

**What this does:**
- Grants `Storage Blob Data Owner` role to the Service Principal
- Allows read/write/delete operations on ADLS Gen2 containers
- Required for uploading data to raw, processed, and curated containers

---

### Step 5: Update Environment Configuration

Edit your `.env` file:

**Remove or comment out:**
```bash
# ADLS_ACCOUNT_KEY=<storage_key>  # ❌ No longer needed!
```

**Add Service Principal credentials:**
```bash
# Service Principal (survives infrastructure changes)
AZURE_CLIENT_ID=27b470a2-fa5d-458a-85d5-e639c0791f23
AZURE_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
```

**Complete `.env` configuration:**
```bash
# ========================================
# AZURE INFRASTRUCTURE CONFIGURATION
# ========================================

# Azure Data Lake Storage Gen2
ADLS_ACCOUNT_NAME=urbancitiesadls2025

# Azure Data Factory
ADF_NAME=urban-cities-adf
ADF_RESOURCE_GROUP=urban-cities-rg

# Azure Subscription
AZURE_SUBSCRIPTION_ID=12f0f306-0cdf-41a6-9028-a7757690a1e2
AZURE_TENANT_ID=edc41ca9-a02a-4623-97cb-2a58f19e3c46

# Service Principal (survives infrastructure changes)
AZURE_CLIENT_ID=27b470a2-fa5d-458a-85d5-e639c0791f23
AZURE_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE

# Azure SQL Database
SQL_SERVER=urban-cities-sql-server.database.windows.net
SQL_DATABASE=urban_cities_db
SQL_USERNAME=sqladmin
SQL_PASSWORD=D030avbang@@
SQL_PORT=1433
```

---

## Testing Authentication

### Test 1: Run Connection Test

```bash
cd "C:\Users\David Ibanga\Data Engineering practicals\Urban_Cities_live_Service\notebook"
python test_azure_connection.py
```

**Expected Output:**
```
============================================================
  TESTING AZURE CONNECTION
============================================================

1. Initializing Azure Data Loader...
INFO:Loading_Azure:Using Service Principal authentication
INFO:Loading_Azure:✓ Azure AD credential authentication active (infrastructure-independent)
   ✓ Azure Data Loader initialized successfully

2. Creating test data...
   ✓ Created test DataFrame with 3 records

3. Testing upload to ADLS raw container...
INFO:Loading_Azure:Successfully uploaded 3 records to raw container
   ✓ Successfully uploaded to: abfss://raw@urbancitiesadls2025.dfs.core.windows.net/...

4. Testing upload to ADLS processed container...
INFO:Loading_Azure:Successfully uploaded 3 records to processed container
   ✓ Successfully uploaded to: abfss://processed@urbancitiesadls2025.dfs.core.windows.net/...

5. Azure Configuration:
   Storage Account: urbancitiesadls2025
   Subscription ID: 12f0f306-0cdf-41a6-9028-a7757690a1e2
   Resource Group: urban-cities-rg
   ADF Name: urban-cities-adf
   Containers: raw, processed, curated

============================================================
  ✓ ALL TESTS PASSED!
============================================================
```

### Test 2: Verify Authentication Method

Check the logs - you should see:
```
INFO:Loading_Azure:Using Service Principal authentication
INFO:Loading_Azure:✓ Azure AD credential authentication active (infrastructure-independent)
```

**NOT:**
```
WARNING:Loading_Azure:⚠ Using storage account key (will break on infrastructure rebuild)
```

### Test 3: Infrastructure Resilience Test

To verify the authentication survives infrastructure changes:

1. **Destroy infrastructure** (optional - only if you want to test):
   ```bash
   cd ../terraform
   terraform destroy
   ```

2. **Recreate infrastructure:**
   ```bash
   terraform apply
   ```

3. **Run test again** - should still work without updating `.env`!

---

## Troubleshooting

### Issue 1: "Please run 'az login'"

**Error:**
```
Please run 'az login' to setup account.
```

**Solution:**
```bash
az login --tenant edc41ca9-a02a-4623-97cb-2a58f19e3c46
```

---

### Issue 2: "AuthorizationPermissionMismatch"

**Error:**
```
AuthorizationPermissionMismatch: This request is not authorized to perform this operation
```

**Solution:**
Ensure Storage Blob Data Owner role is assigned:
```bash
az role assignment create \
  --assignee <YOUR_APP_ID> \
  --role 'Storage Blob Data Owner' \
  --scope '/subscriptions/.../storageAccounts/urbancitiesadls2025'
```

---

### Issue 3: "Invalid client secret"

**Error:**
```
AADSTS7000215: Invalid client secret provided
```

**Solution:**
- Verify `AZURE_CLIENT_SECRET` in `.env` is correct
- Check for extra spaces or line breaks
- If secret is lost, create a new Service Principal

---

### Issue 4: Service Principal Already Exists

**Error:**
```
Another object with the same value for property displayName already exists
```

**Solution:**
Either:
1. Use a different name: `urban-cities-etl-sp-2`
2. Or delete the existing SP:
   ```bash
   az ad sp delete --id <APP_ID>
   ```

---

### Issue 5: "Missing expression after unary operator"

**Error:**
```
Missing expression after unary operator '--'
```

**Solution:**
You're in PowerShell but using bash syntax. Use the command as one line:
```bash
az role assignment create --assignee <APP_ID> --role 'Storage Blob Data Owner' --scope '...'
```

---

## Security Best Practices

### 1. Protect Service Principal Credentials

**❌ DON'T:**
- Commit `.env` file to Git
- Share credentials in Slack/Teams
- Hardcode credentials in code
- Store in plain text files

**✅ DO:**
- Use `.gitignore` for `.env` file
- Store in Azure Key Vault (production)
- Use environment variables in CI/CD
- Rotate credentials periodically

---

### 2. Principle of Least Privilege

**Current Setup:**
```
Service Principal: urban-cities-etl-sp
  ├─ Contributor (Resource Group level)
  └─ Storage Blob Data Owner (Storage Account level)
```

**For Production:**
- Consider more restrictive roles
- Limit scope to specific resources
- Regular audit of permissions

---

### 3. Use Azure Key Vault (Production)

Instead of `.env` file:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Connect to Key Vault
credential = DefaultAzureCredential()
client = SecretClient(
    vault_url="https://your-keyvault.vault.azure.net/",
    credential=credential
)

# Retrieve secrets
client_id = client.get_secret("AZURE-CLIENT-ID").value
client_secret = client.get_secret("AZURE-CLIENT-SECRET").value
```

---

### 4. Monitoring and Auditing

**Enable Activity Logs:**
```bash
az monitor activity-log list \
  --resource-group urban-cities-rg \
  --query "[?contains(authorization.action, 'Microsoft.Storage')]"
```

**Track Service Principal Usage:**
- Azure Portal → Azure AD → Enterprise Applications
- Monitor sign-in logs
- Set up alerts for suspicious activity

---

### 5. Credential Rotation

**Recommended Schedule:**
- Development: Every 90 days
- Production: Every 30-60 days

**Rotate Credentials:**
```bash
# Create new credential for existing SP
az ad sp credential reset \
  --id 27b470a2-fa5d-458a-85d5-e639c0791f23
```

---

## Summary

### What We Accomplished:

1. ✅ Created Service Principal: `urban-cities-etl-sp`
2. ✅ Granted Contributor role on resource group
3. ✅ Granted Storage Blob Data Owner on ADLS Gen2
4. ✅ Configured `.env` with Service Principal credentials
5. ✅ Tested authentication successfully
6. ✅ Achieved infrastructure-independent authentication

### Key Credentials:

```bash
Service Principal Name: urban-cities-etl-sp
App ID (Client ID): 27b470a2-fa5d-458a-85d5-e639c0791f23
Password (Client Secret): YOUR_CLIENT_SECRET_HERE
Tenant ID: edc41ca9-a02a-4623-97cb-2a58f19e3c46
```

### Benefits:

🚀 **Infrastructure Independence:**
- Destroy and recreate infrastructure without updating credentials
- No more manual .env updates after Terraform apply/destroy
- Pipeline always works regardless of infrastructure state

🔒 **Production Ready:**
- Microsoft-recommended authentication method
- RBAC-based security
- Suitable for CI/CD pipelines
- Auditable and monitorable

🎯 **Developer Friendly:**
- One-time setup
- Clear error messages
- Easy to test and debug

---

## Next Steps

1. **Create ADF Pipeline** - For copying data to SQL Database
2. **Create SQL Table Schema** - For storing processed data
3. **Test Complete ETL Workflow** - End-to-end pipeline
4. **Deploy Airflow** - Automate the pipeline
5. **Set Up Monitoring** - Azure Monitor and alerts

---

## References

- [Azure Service Principals Documentation](https://learn.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals)
- [Azure RBAC Roles](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles)
- [Azure Key Vault Best Practices](https://learn.microsoft.com/en-us/azure/key-vault/general/best-practices)
- [Azure Storage Authentication](https://learn.microsoft.com/en-us/azure/storage/common/storage-auth)

---

**Document Version:** 1.0  
**Last Tested:** November 4, 2025  
**Status:** ✅ Production Ready
