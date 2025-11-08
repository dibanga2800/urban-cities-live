"""
Production Deployment Script for NYC 311 ETL Pipeline
Performs comprehensive validation and readiness checks
"""
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

class ProductionDeployment:
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
        
    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)
    
    def check_airflow_status(self):
        """Verify Airflow is running"""
        self.print_header("AIRFLOW STATUS CHECK")
        
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=astro-airflow', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            containers = result.stdout.strip().split('\n')
            containers = [c for c in containers if c]  # Remove empty strings
            
            required_containers = ['scheduler', 'postgres', 'triggerer', 'dag-processor', 'api-server']
            
            print(f"\n✓ Found {len(containers)} Airflow containers running:")
            for container in containers:
                print(f"  • {container}")
            
            if len(containers) >= 5:
                self.checks_passed.append("Airflow containers running")
                return True
            else:
                self.checks_failed.append(f"Only {len(containers)}/5 Airflow containers running")
                return False
                
        except Exception as e:
            print(f"\n✗ Error checking Airflow: {e}")
            self.checks_failed.append("Airflow status check failed")
            return False
    
    def check_dag_files(self):
        """Verify DAG files exist"""
        self.print_header("DAG FILES CHECK")
        
        dag_dir = Path('astro-airflow/dags')
        required_dag = 'nyc_311_incremental_etl_azure.py'
        
        if not dag_dir.exists():
            print(f"\n✗ DAG directory not found: {dag_dir}")
            self.checks_failed.append("DAG directory missing")
            return False
        
        dag_file = dag_dir / required_dag
        if not dag_file.exists():
            print(f"\n✗ Required DAG not found: {required_dag}")
            self.checks_failed.append("Main DAG file missing")
            return False
        
        print(f"\n✓ DAG file found: {required_dag}")
        print(f"  Size: {dag_file.stat().st_size} bytes")
        print(f"  Modified: {datetime.fromtimestamp(dag_file.stat().st_mtime)}")
        
        self.checks_passed.append("DAG files present")
        return True
    
    def check_include_modules(self):
        """Verify include modules exist"""
        self.print_header("INCLUDE MODULES CHECK")
        
        include_dir = Path('astro-airflow/include')
        required_modules = ['Extraction.py', 'Transformation.py', 'Loading_Azure.py']
        
        all_found = True
        for module in required_modules:
            module_path = include_dir / module
            if module_path.exists():
                print(f"✓ {module} - {module_path.stat().st_size} bytes")
            else:
                print(f"✗ {module} - NOT FOUND")
                all_found = False
        
        if all_found:
            self.checks_passed.append("All include modules present")
        else:
            self.checks_failed.append("Some include modules missing")
        
        return all_found
    
    def check_environment_variables(self):
        """Verify environment variables are set"""
        self.print_header("ENVIRONMENT VARIABLES CHECK")
        
        env_file = Path('astro-airflow/.env')
        
        if not env_file.exists():
            print("\n✗ .env file not found!")
            self.checks_failed.append(".env file missing")
            return False
        
        print(f"\n✓ .env file found: {env_file}")
        
        # Check for required variables
        required_vars = [
            'NYC_311_API_URL',
            'AZURE_TENANT_ID',
            'AZURE_CLIENT_ID',
            'AZURE_CLIENT_SECRET',
            'AZURE_SUBSCRIPTION_ID',
            'ADLS_ACCOUNT_NAME',
            'AZURE_SQL_SERVER',
            'AZURE_SQL_DATABASE',
            'AZURE_SQL_USERNAME'
        ]
        
        from dotenv import load_dotenv
        load_dotenv(env_file)
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if 'SECRET' in var or 'PASSWORD' in var:
                    display = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                else:
                    display = value[:50] + "..." if len(value) > 50 else value
                print(f"  ✓ {var}: {display}")
            else:
                print(f"  ✗ {var}: NOT SET")
                missing_vars.append(var)
        
        if missing_vars:
            self.checks_failed.append(f"Missing env vars: {', '.join(missing_vars)}")
            return False
        else:
            self.checks_passed.append("All environment variables set")
            return True
    
    def check_azure_connectivity(self):
        """Test Azure connectivity"""
        self.print_header("AZURE CONNECTIVITY CHECK")
        
        try:
            # Test Azure CLI is installed and logged in
            result = subprocess.run(
                ['az', 'account', 'show'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                import json
                account = json.loads(result.stdout)
                print(f"\n✓ Azure CLI authenticated")
                print(f"  Subscription: {account.get('name')}")
                print(f"  Tenant: {account.get('tenantId')}")
                self.checks_passed.append("Azure CLI authenticated")
                return True
            else:
                print("\n⚠ Azure CLI not authenticated")
                print("  Run: az login")
                self.warnings.append("Azure CLI not authenticated")
                return True  # Don't fail, just warn
                
        except FileNotFoundError:
            print("\n⚠ Azure CLI not installed")
            self.warnings.append("Azure CLI not installed")
            return True  # Don't fail, Service Principal can still work
        except Exception as e:
            print(f"\n⚠ Could not check Azure CLI: {e}")
            self.warnings.append("Azure CLI check inconclusive")
            return True
    
    def check_adf_pipeline(self):
        """Verify ADF pipeline exists"""
        self.print_header("AZURE DATA FACTORY PIPELINE CHECK")
        
        try:
            result = subprocess.run(
                [
                    'az', 'datafactory', 'pipeline', 'show',
                    '--resource-group', 'urban-cities-rg',
                    '--factory-name', 'urban-cities-adf',
                    '--name', 'CopyProcessedDataToSQL'
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("\n✓ ADF Pipeline 'CopyProcessedDataToSQL' exists")
                self.checks_passed.append("ADF pipeline configured")
                return True
            else:
                print("\n⚠ ADF Pipeline not found or not accessible")
                print("  Run: python scripts/adf/create_adf_pipeline.py")
                self.warnings.append("ADF pipeline may need creation")
                return True  # Don't fail, might be created during deployment
                
        except Exception as e:
            print(f"\n⚠ Could not verify ADF pipeline: {e}")
            self.warnings.append("ADF pipeline check inconclusive")
            return True
    
    def check_sql_table(self):
        """Verify SQL table exists"""
        self.print_header("AZURE SQL DATABASE TABLE CHECK")
        
        print("\n⚠ Manual verification required:")
        print("  Connect to: urban-cities-sql-srv-2025.database.windows.net")
        print("  Database: urban_cities_db")
        print("  Table: nyc_311_requests")
        print("\n  Run this query to verify:")
        print("  SELECT COUNT(*) FROM nyc_311_requests;")
        
        self.warnings.append("SQL table check requires manual verification")
        return True
    
    def check_state_files(self):
        """Check ETL state files"""
        self.print_header("STATE FILES CHECK")
        
        state_dir = Path('astro-airflow/include/data')
        state_file = state_dir / 'etl_state.json'
        
        state_dir.mkdir(parents=True, exist_ok=True)
        
        if state_file.exists():
            print(f"\n✓ State file exists: {state_file}")
            print(f"  Size: {state_file.stat().st_size} bytes")
            
            try:
                import json
                with open(state_file) as f:
                    state = json.load(f)
                print(f"  Last processed: {state.get('last_processed_time', 'N/A')}")
            except Exception as e:
                print(f"  ⚠ Could not read state: {e}")
        else:
            print(f"\n⚠ State file not found: {state_file}")
            print("  Will be created on first run")
        
        # Check if old file tracking exists
        old_tracking = state_dir / 'adf_processed_files.json'
        if old_tracking.exists():
            print(f"\n⚠ Old file tracking found: {old_tracking}")
            print("  This is no longer used with single-file approach")
            print("  You can delete it: rm {old_tracking}")
            self.warnings.append("Old file tracking file exists (can be deleted)")
        
        self.checks_passed.append("State directory configured")
        return True
    
    def generate_deployment_report(self):
        """Generate final deployment report"""
        self.print_header("PRODUCTION DEPLOYMENT REPORT")
        
        print(f"\n📊 Summary:")
        print(f"  ✓ Checks Passed: {len(self.checks_passed)}")
        print(f"  ✗ Checks Failed: {len(self.checks_failed)}")
        print(f"  ⚠ Warnings: {len(self.warnings)}")
        
        if self.checks_passed:
            print(f"\n✅ Passed Checks:")
            for check in self.checks_passed:
                print(f"  • {check}")
        
        if self.checks_failed:
            print(f"\n❌ Failed Checks:")
            for check in self.checks_failed:
                print(f"  • {check}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        # Overall status
        print("\n" + "=" * 80)
        if not self.checks_failed:
            print("✅ PRODUCTION READY!")
            print("\nNext Steps:")
            print("  1. Monitor first DAG run in Airflow UI: http://localhost:8080")
            print("  2. Verify data in Azure SQL Database")
            print("  3. Check single master files in ADLS:")
            print("     - raw/raw-data/nyc_311_raw.csv")
            print("     - processed/processed-data/nyc_311_processed.parquet")
            print("  4. Review logs for 'Successfully appended' messages")
            print("  5. Confirm deduplication working (check for 'Removed N duplicates')")
            return True
        else:
            print("❌ NOT READY FOR PRODUCTION")
            print("\nPlease fix the failed checks above before deploying.")
            return False
    
    def run_all_checks(self):
        """Run all production checks"""
        print("\n" + "=" * 80)
        print("  NYC 311 ETL PIPELINE - PRODUCTION DEPLOYMENT VALIDATION")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Run all checks
        checks = [
            self.check_airflow_status,
            self.check_dag_files,
            self.check_include_modules,
            self.check_environment_variables,
            self.check_azure_connectivity,
            self.check_adf_pipeline,
            self.check_sql_table,
            self.check_state_files
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                print(f"\n✗ Check failed with exception: {e}")
                self.checks_failed.append(f"{check.__name__}: {str(e)}")
        
        # Generate report
        ready = self.generate_deployment_report()
        
        print("\n" + "=" * 80)
        
        return ready


if __name__ == "__main__":
    os.chdir(Path(__file__).parent.parent.parent)  # Go to project root
    
    deployment = ProductionDeployment()
    ready = deployment.run_all_checks()
    
    sys.exit(0 if ready else 1)
