"""
Add Firewall Rule to Azure SQL Server
Allows current IP address to connect to the SQL Server
"""
import os
import requests
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_sql_firewall_rule():
    """Add firewall rule for current IP address"""
    
    print("\n" + "="*60)
    print("  AZURE SQL FIREWALL RULE SETUP")
    print("="*60 + "\n")
    
    # Get current IP
    print("Step 1: Getting your public IP address...")
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=10)
        current_ip = response.json()['ip']
        print(f"   ✓ Your IP: {current_ip}\n")
    except Exception as e:
        print(f"   ✗ Could not get IP: {e}")
        return False, None
    
    # Get Azure credentials
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
    resource_group = 'urban-cities-rg'
    server_name = 'urban-cities-sql-server'
    
    print("Step 2: Creating firewall rule via Azure REST API...")
    try:
        # Create credential
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Get access token
        token = credential.get_token("https://management.azure.com/.default")
        
        # Create firewall rule via REST API
        url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Sql/servers/{server_name}/firewallRules/AllowCurrentIP?api-version=2021-11-01"
        
        headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json'
        }
        
        body = {
            'properties': {
                'startIpAddress': current_ip,
                'endIpAddress': current_ip
            }
        }
        
        response = requests.put(url, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        
        print(f"   ✓ Firewall rule created: AllowCurrentIP")
        print(f"   ✓ IP Range: {current_ip} - {current_ip}\n")
        
        print("=" * 60)
        print("  ✓ FIREWALL RULE SETUP COMPLETED!")
        print("=" * 60)
        print("\nYou can now connect to Azure SQL Database")
        print("Waiting 30 seconds for rule to propagate...")
        
        import time
        time.sleep(30)
        
        print("\n✓ Ready to connect!\n")
        return True, current_ip
        
    except Exception as e:
        print(f"\n✗ Error creating firewall rule: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        import traceback
        traceback.print_exc()
        return False, current_ip

if __name__ == "__main__":
    try:
        success, ip = add_sql_firewall_rule()
        if not success:
            print(f"\n⚠ Manual action required:")
            print(f"   Go to Azure Portal → SQL Server → Networking")
            print(f"   Add firewall rule for IP: {ip}")
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Setup failed: {str(e)}")
        exit(1)
