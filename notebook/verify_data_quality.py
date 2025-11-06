import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={os.getenv('SQL_SERVER')};"
    f"DATABASE={os.getenv('SQL_DATABASE')};"
    f"UID={os.getenv('SQL_USERNAME')};"
    f"PWD={os.getenv('SQL_PASSWORD')}"
)

cursor = conn.cursor()

print("\n=== SAMPLE DATA (First 10 rows) ===")
cursor.execute("""
    SELECT TOP 10 
        unique_key, 
        complaint_type, 
        borough, 
        created_date, 
        closed_date, 
        latitude, 
        longitude, 
        data_quality_score 
    FROM nyc_311_requests
    ORDER BY created_date DESC
""")

for row in cursor.fetchall():
    print(f"Key: {row[0]}")
    print(f"  Type: {row[1]}, Borough: {row[2]}")
    print(f"  Created: {row[3]}, Closed: {row[4]}")
    print(f"  Location: ({row[5]}, {row[6]}), Quality Score: {row[7]}")
    print()

print("\n=== NULL VALUE ANALYSIS ===")
cursor.execute("""
    SELECT 
        COUNT(*) as total_rows,
        SUM(CASE WHEN latitude IS NULL THEN 1 ELSE 0 END) as null_latitude,
        SUM(CASE WHEN longitude IS NULL THEN 1 ELSE 0 END) as null_longitude,
        SUM(CASE WHEN borough IS NULL THEN 1 ELSE 0 END) as null_borough,
        SUM(CASE WHEN closed_date IS NULL THEN 1 ELSE 0 END) as null_closed_date,
        SUM(CASE WHEN complaint_type IS NULL THEN 1 ELSE 0 END) as null_complaint_type,
        AVG(data_quality_score) as avg_quality_score
    FROM nyc_311_requests
""")

result = cursor.fetchone()
print(f"Total Rows: {result[0]}")
print(f"Null Latitude: {result[1]} ({result[1]/result[0]*100:.1f}%)")
print(f"Null Longitude: {result[2]} ({result[2]/result[0]*100:.1f}%)")
print(f"Null Borough: {result[3]} ({result[3]/result[0]*100:.1f}%)")
print(f"Null Closed Date: {result[4]} ({result[4]/result[0]*100:.1f}%)")
print(f"Null Complaint Type: {result[5]} ({result[5]/result[0]*100:.1f}%)")
print(f"Average Quality Score: {result[6]:.2f}/100")

print("\n=== DATA TYPE VERIFICATION ===")
cursor.execute("""
    SELECT TOP 5 
        created_date, 
        closed_date, 
        processed_at 
    FROM nyc_311_requests 
    WHERE closed_date IS NOT NULL
""")

print("Datetime formats (should be YYYY-MM-DD HH:MM:SS):")
for row in cursor.fetchall():
    print(f"  Created: {row[0]}, Closed: {row[1]}, Processed: {row[2]}")

conn.close()
print("\n✅ Verification complete!")
