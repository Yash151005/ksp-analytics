from pymongo import MongoClient
from datetime import datetime, timedelta, UTC
import random

client = MongoClient("mongodb://localhost:27017/")
db = client.ksp_analytics

# Remove previous incorrectly formatted anomalies
db.crimes.delete_many({"description": "Anomaly generated crime"})

# Add 30 crimes exactly 5 days ago
anomaly_date = datetime.now(UTC) - timedelta(days=5)
day_str = anomaly_date.strftime("%A").lower()

crimes_to_add = []
for i in range(30):
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    time_str = f"{hour:02d}:{minute:02d}"
    
    crimes_to_add.append({
        "crime_id": f"ANOMALY-{random.randint(1000, 9999)}",
        "type": random.choice(["theft", "assault", "robbery", "cybercrime", "fraud"]),
        "status": "open",
        "severity": random.randint(3, 5),
        "district": "Bangalore",
        "taluk": "Central",
        "latitude": 12.9716 + random.uniform(-0.01, 0.01),
        "longitude": 77.5946 + random.uniform(-0.01, 0.01),
        "date": anomaly_date,
        "time": time_str,
        "day_of_week": day_str,
        "description": "Anomaly generated crime",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    })

db.crimes.insert_many(crimes_to_add)
print(f"Fixed anomalies. Added {len(crimes_to_add)} crimes on {anomaly_date.strftime('%Y-%m-%d')} ({day_str}) with time fields.")
