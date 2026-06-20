"""
Pydantic models for KSP Analytics Platform MongoDB Document Store
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class MongoBaseModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class User(MongoBaseModel):
    username: str
    email: str
    hashed_password: str
    full_name: str
    role: str = "viewer"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Victim(MongoBaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    crime_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Crime(MongoBaseModel):
    crime_id: str
    date: datetime
    time: str
    type: str
    subtype: Optional[str] = None
    district: str
    taluk: Optional[str] = None
    police_station: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    status: str = "open"
    severity: int
    weather: Optional[str] = None
    time_of_day: Optional[str] = None
    day_of_week: Optional[str] = None
    victims: List[Victim] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Criminal(MongoBaseModel):
    name: str
    alias: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    nationality: str = "India"
    aadhaar_hash: Optional[str] = None
    crime_history: Dict[str, Any] = Field(default_factory=dict)
    risk_score: float = 0
    status: str = "active"
    last_known_location: Optional[str] = None
    last_known_latitude: Optional[float] = None
    last_known_longitude: Optional[float] = None
    photo_url: Optional[str] = None
    associated_criminal_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Vehicle(MongoBaseModel):
    license_plate: str
    make_model: str
    color: str
    criminal_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BankAccount(MongoBaseModel):
    account_number: str
    bank_name: str
    balance: float
    criminal_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Alert(MongoBaseModel):
    title: str
    description: str
    severity: str
    crime_id: Optional[str] = None
    affected_area: str
    crime_count_spike: Optional[float] = None
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    ollama_recommendation: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Report(MongoBaseModel):
    title: str
    description: Optional[str] = None
    report_type: str
    date_from: datetime
    date_to: datetime
    districts: List[str] = Field(default_factory=list)
    crime_types: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    narrative_summary: Optional[str] = None
    created_by: Optional[str] = None
    file_path: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AuditLog(MongoBaseModel):
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OllamaAuditLog(MongoBaseModel):
    function_name: str
    input_hash: str
    output: str
    response_time_ms: int
    tokens_generated: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Helper to serialize MongoDB documents
def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc

def serialize_docs(docs: list) -> list:
    return [serialize_doc(doc) for doc in docs]
