"""
Crimes router for KSP Analytics Platform MongoDB
Handles all crime-related endpoints
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from pymongo.database import Database
from bson.objectid import ObjectId
from datetime import datetime, timedelta, UTC
from typing import List, Optional
from database import get_db
from models import serialize_docs, serialize_doc
from services.analytics_service import get_crime_summary, get_district_stats, get_crime_trend
from services.export_service import export_crimes_to_csv

router = APIRouter(prefix="/api/crimes", tags=["crimes"])


@router.get("/")
def list_crimes(
    district: Optional[str] = Query(None),
    crime_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    severity: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Database = Depends(get_db),
):
    """List crimes with filtering and pagination"""
    filter_query = {}
    
    if district:
        filter_query["district"] = district
    
    if crime_type:
        filter_query["type"] = crime_type
    
    if status:
        filter_query["status"] = status
    
    if severity is not None:
        filter_query["severity"] = severity
    
    date_filter = {}
    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from)
            date_filter["$gte"] = from_date
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format")
    
    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to)
            date_filter["$lte"] = to_date
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format")
            
    if date_filter:
        filter_query["date"] = date_filter
    
    total = db.crimes.count_documents(filter_query)
    cursor = db.crimes.find(filter_query).sort("date", -1).skip(offset).limit(limit)
    crimes = list(cursor)
    
    # Map _id to id and ensure date is isoformat string
    formatted_crimes = []
    for c in crimes:
        c["id"] = str(c.pop("_id"))
        if "date" in c and isinstance(c["date"], datetime):
            c["date"] = c["date"].isoformat()
        formatted_crimes.append(c)
    
    return {
        "data": formatted_crimes,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{crime_id}")
def get_crime(crime_id: str, db: Database = Depends(get_db)):
    """Get crime details by ID"""
    try:
        obj_id = ObjectId(crime_id)
        filter_cond = {"$or": [{"_id": obj_id}, {"crime_id": crime_id}]}
    except:
        filter_cond = {"crime_id": crime_id}
        
    crime = db.crimes.find_one(filter_cond)
    if not crime:
        raise HTTPException(status_code=404, detail="Crime not found")
    
    if "date" in crime and isinstance(crime["date"], datetime):
        crime["date"] = crime["date"].isoformat()
        
    return serialize_doc(crime)


@router.get("/stats/summary")
def get_summary(days: int = Query(30, ge=1, le=365), db: Database = Depends(get_db)):
    """Get crime statistics summary"""
    return get_crime_summary(days)


@router.get("/stats/by-district")
def get_by_district(days: int = Query(30, ge=1, le=365), db: Database = Depends(get_db)):
    """Get crime statistics by district"""
    return get_district_stats(days)


@router.get("/stats/by-type")
def get_by_type(days: int = Query(30, ge=1, le=365), db: Database = Depends(get_db)):
    """Get crime statistics by type using MongoDB Aggregation"""
    cutoff_date = datetime.now(UTC) - timedelta(days=days)
    
    pipeline = [
        {"$match": {"date": {"$gte": cutoff_date}}},
        {"$group": {"_id": "$type", "count": {"$sum": 1}}}
    ]
    
    type_stats = list(db.crimes.aggregate(pipeline))
    return {item["_id"]: item["count"] for item in type_stats}


@router.get("/stats/trend")
def get_trend(months: int = Query(12, ge=1, le=60), db: Database = Depends(get_db)):
    """Get crime trend over time"""
    return get_crime_trend(months)


@router.get("/hotspots")
def get_hotspots(db: Database = Depends(get_db)):
    """Get identified crime hotspots"""
    from services.analytics_service import get_high_risk_zones
    return get_high_risk_zones()


@router.get("/export/csv")
def export_csv(
    district: Optional[str] = Query(None),
    crime_type: Optional[str] = Query(None),
    db: Database = Depends(get_db),
):
    """Export crimes to CSV"""
    filter_query = {}
    
    if district:
        filter_query["district"] = district
    
    if crime_type:
        filter_query["type"] = crime_type
    
    crimes = list(db.crimes.find(filter_query).limit(10000))
    csv_data = export_crimes_to_csv(crimes)
    
    return {
        "filename": f"crimes_export_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv",
        "data": csv_data,
    }
