"""
Database configuration and setup for KSP Analytics Platform
"""
from pymongo import MongoClient
import os

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

client = MongoClient(MONGO_URI)
db_instance = client.ksp_analytics

def get_db():
    """Dependency for getting DB session in FastAPI routes"""
    yield db_instance

def init_db():
    """Initialize database indexes"""
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
