"""
Database configuration and setup for KSP Analytics Platform
"""
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_mongo_uri():
    return os.getenv("MONGO_URI", "mongodb+srv://codebidteam102_db_user:12345@cluster0.oyl9icq.mongodb.net/?appName=Cluster0")

client = None
db_instance = None

def init_client():
    global client, db_instance
    if client is not None:
        return client
        
    try:
        uri = get_mongo_uri()
        if not uri.startswith(("mongodb://", "mongodb+srv://")):
            uri = "mongodb+srv://" + uri
        # Instantiate without blocking if possible
        client = MongoClient(uri, serverSelectionTimeoutMS=3000, connect=False)
    except Exception as e:
        print(f"Warning: Invalid MONGO_URI. Using fallback. Error: {e}")
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000, connect=False)
        
    db_instance = client.ksp_analytics
    return client

def get_db():
    """Dependency for getting DB session in FastAPI routes"""
    init_client()
    yield db_instance

def get_db_instance():
    init_client()
    return db_instance

def init_db():
    """Initialize database indexes"""
    init_client()
    # Ping first to fail fast if no DB is available
    client.admin.command('ping')
    # Create required indexes
    db_instance.users.create_index("username", unique=True)
    db_instance.users.create_index("email", unique=True)
    db_instance.crimes.create_index("crime_id", unique=True)
    db_instance.crimes.create_index("date")
    db_instance.crimes.create_index("district")
    db_instance.crimes.create_index("type")
    db_instance.criminals.create_index("aadhaar_hash", unique=True, sparse=True)
    db_instance.criminals.create_index("risk_score")
    db_instance.alerts.create_index("severity")
    db_instance.alerts.create_index("created_at")

def drop_all_tables():
    """Drop all tables (for dev/testing)"""
    client.drop_database("ksp_analytics")
