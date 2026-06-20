from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import random

client = MongoClient("mongodb://localhost:27017/")
db = client.ksp_analytics

# Add 30 crimes exactly 5 days ago to create a massive anomaly
anomaly_date = datetime.now(timezone.utc) - timedelta(days=5)

crimes_to_add = []
for i in range(30):
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
        "description": "Anomaly generated crime",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    })

db.crimes.insert_many(crimes_to_add)
print(f"Added {len(crimes_to_add)} crimes on {anomaly_date.strftime('%Y-%m-%d')} to simulate an anomaly.")
