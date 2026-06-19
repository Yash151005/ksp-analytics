"""
Seed data generator for KSP Analytics Platform
Creates realistic crime records across Karnataka in MongoDB
"""
import random
from datetime import datetime, timedelta, UTC
from passlib.context import CryptContext
from bson.objectid import ObjectId

from database import db_instance, init_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = db_instance

# Karnataka Districts with coordinates (lat, lng)
DISTRICTS = {
    "Bengaluru Urban": (12.9716, 77.5946),
    "Bengaluru Rural": (12.7500, 77.7500),
    "Ramanagara": (12.7667, 77.6167),
    "Kolar": (13.1667, 78.1333),
    "Chikballapur": (13.3167, 78.2833),
    "Tumakuru": (13.2167, 77.1167),
    "Davanagere": (14.4667, 75.9333),
    "Shivamogga": (13.7500, 75.5667),
    "Uttara Kannada": (14.2500, 74.6667),
    "Chikmagalur": (13.3167, 75.7500),
    "Kodagu": (12.4167, 75.7500),
    "Hassan": (13.0033, 75.9333),
    "Mysuru": (12.3050, 75.8150),
    "Mandya": (12.5167, 76.1833),
    "Chamrajnagar": (11.9167, 76.7667),
    "Bangalore Headquarters": (13.1939, 77.6245),
    "Belagavi": (15.8497, 75.6278),
    "Bailhongal": (15.8500, 75.6500),
    "Belgaum": (15.8500, 75.6500),
    "Bagalkot": (16.1667, 75.7167),
    "Gadag": (14.8333, 75.3333),
    "Haveri": (14.7833, 75.4000),
    "Bellary": (15.1667, 76.9333),
    "Ballari": (15.1667, 76.9333),
    "Raichur": (16.2167, 77.3667),
    "Kalaburagi": (17.3333, 76.8333),
    "Bidar": (17.9167, 77.5167),
    "Yadgir": (16.7667, 77.1333),
    "Udupi": (13.3333, 74.7500),
    "Mangaluru": (12.8656, 74.8663),
    "Dakshina Kannada": (13.0084, 74.8477),
    "Kasaragod": (12.5000, 75.0000),
}

TALUKS = {
    "Bengaluru Urban": ["Bengaluru South", "Bengaluru North", "Bengaluru East", "Bengaluru West"],
    "Bengaluru Rural": ["Whitefield", "Sarjapur", "Devanahalli"],
    "Mysuru": ["Mysuru", "Hunsur", "Nanjangud", "Heggadadevanakote"],
    "Belagavi": ["Belagavi", "Soundatti", "Bailhongal", "Ramdurg"],
    "Ballari": ["Ballari", "Harpanahalli", "Hospet", "Kudligi"],
    "Kalaburagi": ["Kalaburagi", "Aland", "Afzalpur", "Gulbarga"],
    "Mangaluru": ["Mangaluru", "Moodabidri", "Bantwal"],
    "Shivamogga": ["Shivamogga", "Bhadravati", "Sagar"],
}

POLICE_STATIONS = [
    "Bengaluru City Police", "Whitefield Police", "Koramangala Police",
    "Mysuru City Police", "Hubli Police", "Belagavi Police",
    "Mangaluru City Police", "Ballari Police", "Bidar Police",
    "Raichur Police", "Tumakuru Police", "Kalaburagi Police",
]

CRIME_TYPES = [
    ("theft", ["vehicle theft", "house burglary", "shoplifting", "pickpocketing", "armed robbery"]),
    ("assault", ["physical assault", "domestic violence", "street brawl", "stabbing", "beating"]),
    ("fraud", ["credit card fraud", "cheque bounce", "online scam", "identity theft", "forgery"]),
    ("kidnapping", ["child abduction", "ransom kidnapping", "elopement case", "trafficking"]),
    ("murder", ["premeditated murder", "crime of passion", "gangland killing", "hit and run"]),
    ("cybercrime", ["online fraud", "phishing", "malware", "ransomware", "hacking"]),
    ("drugs", ["possession", "trafficking", "manufacturing", "substance abuse", "drug dealing"]),
]

# Indian names (mix of Kannada, Hindi, Urdu)
FIRST_NAMES = [
    "Rajesh", "Kumar", "Mohammed", "Vikram", "Arjun", "Arun", "Suresh",
    "Ramesh", "Harish", "Ashok", "Pawan", "Nikhil", "Rohan", "Varun",
    "Deepak", "Sandeep", "Karthik", "Shiva", "Sanjay", "Dinesh",
    "Praveen", "Naveen", "Prakash", "Mahesh", "Ravi", "Vishal",
    "Karim", "Hassan", "Ibrahim", "Ali", "Ahmed", "Omar", "Hussain",
    "Khalid", "Imran", "Faisal", "Rashid",
]

LAST_NAMES = [
    "Singh", "Kumar", "Sharma", "Gupta", "Patel", "Reddy", "Rao",
    "Khan", "Mohammad", "Ahmed", "Hassan", "Ali", "Ibrahim",
    "Verma", "Pandey", "Mishra", "Agarwal", "Desai", "Iyer",
    "Nair", "Menon", "Bhat", "Kulkarni", "Joshi", "Dikshit",
]

ALIASES = [
    "Sunny", "Rocky", "Tiger", "Bullet", "Ghost", "Shocker", "Viper",
    "Rogue", "Shadow", "Phoenix", "Blade", "Storm", "Hawk", "Eagle",
]

OCCUPATIONS = [
    "Laborer", "Driver", "Shopkeeper", "Student", "Unemployed",
    "Security Guard", "Factory Worker", "Street Vendor", "Hawker",
]

WEATHER_CONDITIONS = ["clear", "rainy", "cloudy", "foggy", "stormy"]
TIMES_OF_DAY = ["morning", "afternoon", "evening", "night"]
DAYS_OF_WEEK = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

VEHICLE_MAKES = ["Toyota Innova", "Mahindra Scorpio", "Maruti Swift", "Hyundai Creta", "Honda City", "Tata Nexon"]
VEHICLE_COLORS = ["White", "Black", "Silver", "Red", "Grey"]
BANK_NAMES = ["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank", "Bank of Baroda"]


def get_random_coordinates(district_name):
    """Get realistic coordinates within a district"""
    district_coords = DISTRICTS.get(district_name, (13.0, 77.0))
    lat = district_coords[0] + random.uniform(-0.5, 0.5)
    lng = district_coords[1] + random.uniform(-0.5, 0.5)
    lat = max(11.5, min(18.5, lat))
    lng = max(74.0, min(78.5, lng))
    return lat, lng


def generate_crime_id():
    """Generate KSP-format crime ID"""
    year = random.randint(2022, 2026)
    sequence = random.randint(1000, 9999)
    return f"KSP-{year}-{sequence:05d}"


def create_default_users():
    """Create default demo users"""
    now = datetime.now(UTC)
    users = [
        {
            "username": "admin",
            "email": "admin@ksp.gov.in",
            "hashed_password": pwd_context.hash("admin123"),
            "full_name": "Admin User",
            "role": "admin",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "username": "analyst",
            "email": "analyst@ksp.gov.in",
            "hashed_password": pwd_context.hash("analyst123"),
            "full_name": "Crime Analyst",
            "role": "analyst",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "username": "investigator",
            "email": "investigator@ksp.gov.in",
            "hashed_password": pwd_context.hash("inv123"),
            "full_name": "Police Investigator",
            "role": "investigator",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "username": "viewer",
            "email": "viewer@ksp.gov.in",
            "hashed_password": pwd_context.hash("view123"),
            "full_name": "Data Viewer",
            "role": "viewer",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
    ]
    db.users.insert_many(users)
    return users


def create_criminals(count=100):
    """Generate criminal records with network connections"""
    criminals = []
    now = datetime.now(UTC)
    
    for i in range(count):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        name = f"{first_name} {last_name}"
        
        criminal = {
            "_id": ObjectId(),
            "name": name,
            "alias": f"{random.choice(ALIASES)}-{i}",
            "age": random.randint(18, 70),
            "gender": random.choice(["M", "F"]),
            "nationality": "India",
            "crime_history": [],
            "risk_score": random.uniform(0, 100),
            "status": random.choice(["active", "arrested", "absconding"]),
            "last_known_location": random.choice(list(DISTRICTS.keys())),
            "last_known_latitude": random.uniform(11.5, 18.5),
            "last_known_longitude": random.uniform(74.0, 78.5),
            "photo_url": f"/assets/criminal_{i}.jpg" if random.random() > 0.5 else None,
            "associated_criminal_ids": [],
            "created_at": now,
            "updated_at": now
        }
        aadhaar_hash = f"AADHAAR_{i:06d}" if random.random() > 0.2 else None
        if aadhaar_hash:
            criminal["aadhaar_hash"] = aadhaar_hash
        criminals.append(criminal)
    
    # Create network connections between criminals
    for criminal in criminals:
        num_associates = random.randint(0, 5)
        if num_associates > 0:
            associates = random.sample(
                [c for c in criminals if c["_id"] != criminal["_id"]],
                min(num_associates, len(criminals) - 1)
            )
            for associate in associates:
                assoc_id = str(associate["_id"])
                if assoc_id not in criminal["associated_criminal_ids"]:
                    criminal["associated_criminal_ids"].append(assoc_id)
    
    db.criminals.insert_many(criminals)
    return criminals


def create_crimes(criminals, count=600):
    """Generate crime records with victims"""
    crimes = []
    crime_ids_set = set()
    now = datetime.now(UTC)
    
    for i in range(count):
        while True:
            crime_id = generate_crime_id()
            if crime_id not in crime_ids_set:
                crime_ids_set.add(crime_id)
                break
        
        district = random.choice(list(DISTRICTS.keys()))
        taluk = random.choice(TALUKS.get(district, ["Main"]))
        crime_type, subtypes = random.choice(CRIME_TYPES)
        subtype = random.choice(subtypes)
        
        lat, lng = get_random_coordinates(district)
        
        days_ago = random.randint(0, 365 * 3)
        crime_date = datetime.now(UTC) - timedelta(days=days_ago)
        
        # Create victims
        victims = []
        num_victims = random.randint(0, 3)
        for _ in range(num_victims):
            victims.append({
                "age": random.randint(5, 90),
                "gender": random.choice(["M", "F"]),
                "occupation": random.choice(OCCUPATIONS) if random.random() > 0.3 else None,
                "created_at": now
            })
            
        crime = {
            "crime_id": crime_id,
            "date": crime_date,
            "time": f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}",
            "type": crime_type,
            "subtype": subtype,
            "district": district,
            "taluk": taluk,
            "police_station": random.choice(POLICE_STATIONS),
            "latitude": lat,
            "longitude": lng,
            "description": f"{subtype.title()} incident in {district}. Details under investigation.",
            "status": random.choice(["open", "closed", "under_investigation"]),
            "severity": random.randint(1, 5),
            "weather": random.choice(WEATHER_CONDITIONS),
            "time_of_day": random.choice(TIMES_OF_DAY),
            "day_of_week": random.choice(DAYS_OF_WEEK),
            "victims": victims,
            "created_at": now,
            "updated_at": now
        }
        crimes.append(crime)
    
    db.crimes.insert_many(crimes)
    return crimes


def create_alerts(crimes, count=50):
    """Generate alert records"""
    alerts = []
    now = datetime.now(UTC)
    
    for i in range(count):
        crime = random.choice(crimes)
        
        alert = {
            "title": f"{crime['type'].title()} Spike in {crime['district']}",
            "description": f"Unusual increase in {crime['type']} incidents detected in {crime['district']}",
            "severity": random.choice(["critical", "high", "medium", "low"]),
            "crime_id": str(crime.get("_id", crime["crime_id"])), # Just a reference string
            "affected_area": crime["district"],
            "crime_count_spike": random.uniform(10, 150),
            "is_acknowledged": random.random() > 0.6,
            "ollama_recommendation": f"Increase patrols in {crime['district']}. Deploy additional officers to high-risk areas.",
            "created_at": now,
            "updated_at": now
        }
        alerts.append(alert)
    
    if alerts:
        db.alerts.insert_many(alerts)
    return alerts


def create_reports(count=15):
    """Generate dummy reports"""
    reports = []
    now = datetime.now(UTC)
    report_types = ["daily", "weekly", "monthly", "custom"]
    
    for i in range(count):
        r_type = random.choice(report_types)
        reports.append({
            "title": f"Crime Analytics {r_type.title()} Report #{i+100}",
            "description": f"Auto-generated {r_type} report for district analysis",
            "report_type": r_type,
            "date_from": now - timedelta(days=30),
            "date_to": now,
            "districts": random.sample(list(DISTRICTS.keys()), k=random.randint(1, 3)),
            "crime_types": random.sample(["theft", "assault", "fraud", "murder", "drugs"], k=random.randint(1, 3)),
            "metrics": {
                "total_crimes": random.randint(50, 500),
                "resolved_cases": random.randint(10, 200),
                "arrests_made": random.randint(5, 100)
            },
            "narrative_summary": "This is a seeded dummy report for testing purposes. It shows general crime trends.",
            "created_by": "admin",
            "created_at": now - timedelta(days=random.randint(0, 30))
        })
    
    if reports:
        db.reports.insert_many(reports)
    return reports


def create_audit_logs(count=50):
    """Generate dummy audit logs"""
    logs = []
    now = datetime.now(UTC)
    actions = ["LOGIN", "VIEW_REPORT", "GENERATE_REPORT", "UPDATE_ALERT", "CREATE_USER", "EXPORT_DATA"]
    resources = ["System", "Report", "Alert", "User", "CrimeData"]
    
    for i in range(count):
        logs.append({
            "user_id": "admin",
            "action": random.choice(actions),
            "resource_type": random.choice(resources),
            "resource_id": f"RES-{random.randint(1000, 9999)}",
            "details": {"note": "Automated seeded log"},
            "ip_address": f"192.168.1.{random.randint(1, 255)}",
            "created_at": now - timedelta(hours=random.randint(1, 720))
        })
    
    if logs:
        db.audit_logs.insert_many(logs)
    return logs


def create_vehicles(criminals, count=80):
    """Generate vehicle records"""
    vehicles = []
    now = datetime.now(UTC)
    for _ in range(count):
        criminal = random.choice(criminals)
        vehicles.append({
            "license_plate": f"KA-{random.randint(1, 60):02d}-{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}-{random.randint(1000, 9999)}",
            "make_model": random.choice(VEHICLE_MAKES),
            "color": random.choice(VEHICLE_COLORS),
            "criminal_id": str(criminal["_id"]),
            "created_at": now
        })
    if vehicles:
        db.vehicles.insert_many(vehicles)
    return vehicles


def create_bank_accounts(criminals, count=60):
    """Generate bank account records"""
    accounts = []
    now = datetime.now(UTC)
    for _ in range(count):
        criminal = random.choice(criminals)
        accounts.append({
            "account_number": f"{random.randint(1000000000, 9999999999)}",
            "bank_name": random.choice(BANK_NAMES),
            "balance": round(random.uniform(1000.0, 500000.0), 2),
            "criminal_id": str(criminal["_id"]),
            "created_at": now
        })
    if accounts:
        db.bank_accounts.insert_many(accounts)
    return accounts


def seed_database():
    """Main function to populate database with seed data"""
    print("🌱 Starting MongoDB database seeding...")
    
    # Drop existing collections first for clean seeding
    print("🗑️ Dropping existing collections...")
    db.users.drop()
    db.criminals.drop()
    db.crimes.drop()
    db.alerts.drop()
    db.reports.drop()
    db.audit_logs.drop()
    db.ollama_audit_logs.drop()
    db.vehicles.drop()
    db.bank_accounts.drop()
    
    # Initialize indexes
    print("📋 Creating indexes...")
    init_db()
    
    try:
        # Create default users
        print("👤 Creating default users...")
        users = create_default_users()
        print(f"✓ Created {len(users)} users")
        
        # Create criminals
        print("👮 Creating criminal records...")
        criminals = create_criminals(count=150)
        print(f"✓ Created {len(criminals)} criminal records with network associations")
        
        # Create crimes
        print("🚨 Creating crime incidents...")
        crimes = create_crimes(criminals, count=600)
        print(f"✓ Created {len(crimes)} crime records with victims")
        
        # Create alerts
        print("🚨 Creating crime alerts...")
        alerts = create_alerts(crimes, count=60)
        print(f"✓ Created {len(alerts)} alert records")
        
        # Create reports
        print("📄 Creating dummy reports...")
        reports = create_reports(count=15)
        print(f"✓ Created {len(reports)} report records")
        
        # Create audit logs
        print("📋 Creating dummy audit logs...")
        logs = create_audit_logs(count=50)
        print(f"✓ Created {len(logs)} audit log records")
        
        # Create vehicles and bank accounts
        print("🚗 Creating vehicle records...")
        vehicles = create_vehicles(criminals, count=80)
        print(f"✓ Created {len(vehicles)} vehicle records")
        
        print("🏦 Creating bank account records...")
        bank_accounts = create_bank_accounts(criminals, count=60)
        print(f"✓ Created {len(bank_accounts)} bank account records")
        
        # Update criminal records with crime history
        print("📊 Linking criminals to crimes...")
        
        # Refetch crimes to get object IDs if needed, but we can just use the memory ones
        # Actually crimes returned from insert_many have _id added to them by pymongo
        
        for criminal in criminals:
            num_crimes = random.randint(0, 8)
            if num_crimes > 0:
                assigned_crimes = random.sample(crimes, min(num_crimes, len(crimes)))
                crime_history = [
                    {
                        "crime_id": c["crime_id"],
                        "type": c["type"],
                        "date": c["date"].isoformat(),
                        "status": c["status"],
                    }
                    for c in assigned_crimes
                ]
                
                risk_score = min(100, 10 + (len(crime_history) * 8))
                
                db.criminals.update_one(
                    {"_id": criminal["_id"]},
                    {"$set": {
                        "crime_history": crime_history,
                        "risk_score": risk_score
                    }}
                )
        
        print("✓ Updated criminal records with crime history and risk scores")
        
        print("\n✅ Database seeding complete!")
        print(f"Summary:")
        print(f"  - {len(users)} users")
        print(f"  - {len(criminals)} criminals")
        print(f"  - {len(crimes)} crimes")
        print(f"  - {len(alerts)} alerts")
        print(f"  - {len(reports)} reports")
        print(f"  - {len(logs)} audit logs")
        print(f"  - {len(vehicles)} vehicles")
        print(f"  - {len(bank_accounts)} bank accounts")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        raise


if __name__ == "__main__":
    seed_database()
