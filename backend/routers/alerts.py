"""
Alerts router for KSP Analytics Platform MongoDB
Handles all alert and notification endpoints
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from pymongo.database import Database
from bson.objectid import ObjectId
from typing import Optional
from datetime import datetime, timedelta, timezone
from database import get_db
from models import serialize_docs, serialize_doc
from services.export_service import export_alerts_to_csv
import re

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/")
def list_alerts(
    severity: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    days: int = Query(30, ge=1, le=90),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Database = Depends(get_db),
):
    """List alerts with filtering and pagination"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    filter_query = {"created_at": {"$gte": cutoff_date}}
    
    if severity:
        filter_query["severity"] = severity
    
    if district:
        filter_query["affected_area"] = re.compile(f".*{district}.*", re.IGNORECASE)
    
    if acknowledged is not None:
        filter_query["is_acknowledged"] = acknowledged
    
    total = db.alerts.count_documents(filter_query)
    alerts = list(db.alerts.find(filter_query).sort("created_at", -1).skip(offset).limit(limit))
    
    data = []
    for a in alerts:
        data.append({
            "id": str(a["_id"]),
            "title": a.get("title"),
            "description": a.get("description"),
            "severity": a.get("severity"),
            "affected_area": a.get("affected_area"),
            "crime_count_spike": a.get("crime_count_spike"),
            "is_acknowledged": a.get("is_acknowledged", False),
            "ollama_recommendation": a.get("ollama_recommendation"),
            "created_at": a.get("created_at").isoformat() if isinstance(a.get("created_at"), datetime) else a.get("created_at"),
            "updated_at": a.get("updated_at").isoformat() if isinstance(a.get("updated_at"), datetime) else a.get("updated_at"),
        })
    
    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{alert_id}")
def get_alert(alert_id: str, db: Database = Depends(get_db)):
    """Get alert details by ID"""
    try:
        obj_id = ObjectId(alert_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid alert ID format")
        
    alert = db.alerts.find_one({"_id": obj_id})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    result = serialize_doc(alert)
    if "created_at" in result and isinstance(result["created_at"], datetime):
        result["created_at"] = result["created_at"].isoformat()
    if "updated_at" in result and isinstance(result["updated_at"], datetime):
        result["updated_at"] = result["updated_at"].isoformat()
        
    return result


@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, db: Database = Depends(get_db)):
    """Mark alert as acknowledged"""
    try:
        obj_id = ObjectId(alert_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid alert ID format")
        
    now = datetime.now(timezone.utc)
    result = db.alerts.update_one(
        {"_id": obj_id},
        {"$set": {"is_acknowledged": True, "updated_at": now}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "message": "Alert acknowledged",
        "alert_id": alert_id,
        "updated_at": now.isoformat(),
    }


@router.post("/{alert_id}/escalate")
def escalate_alert(alert_id: str, db: Database = Depends(get_db)):
    """Escalate alert severity"""
    try:
        obj_id = ObjectId(alert_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid alert ID format")
        
    alert = db.alerts.find_one({"_id": obj_id})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    severity_levels = ["low", "medium", "high", "critical"]
    current_severity = alert.get("severity", "low").lower()
    
    try:
        current_index = severity_levels.index(current_severity)
    except ValueError:
        current_index = 0
        
    now = datetime.now(timezone.utc)
    if current_index < len(severity_levels) - 1:
        new_severity = severity_levels[current_index + 1]
        db.alerts.update_one(
            {"_id": obj_id},
            {"$set": {"severity": new_severity, "updated_at": now}}
        )
    else:
        new_severity = current_severity
        
    return {
        "message": "Alert escalated",
        "alert_id": alert_id,
        "new_severity": new_severity,
        "updated_at": now.isoformat(),
    }


@router.get("/stats/summary")
def get_summary(db: Database = Depends(get_db)):
    """Get alert statistics"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    total_alerts = db.alerts.count_documents({"created_at": {"$gte": cutoff_date}})
    
    critical_alerts = db.alerts.count_documents({
        "severity": "critical",
        "created_at": {"$gte": cutoff_date}
    })
    
    high_alerts = db.alerts.count_documents({
        "severity": "high",
        "created_at": {"$gte": cutoff_date}
    })
    
    acknowledged = db.alerts.count_documents({
        "is_acknowledged": True,
        "created_at": {"$gte": cutoff_date}
    })
    
    unacknowledged = total_alerts - acknowledged
    
    pipeline = [
        {"$match": {"created_at": {"$gte": cutoff_date}}},
        {"$group": {"_id": "$affected_area", "count": {"$sum": 1}}}
    ]
    affected_areas = list(db.alerts.aggregate(pipeline))
    
    return {
        "total_alerts_7d": total_alerts,
        "critical_count": critical_alerts,
        "high_count": high_alerts,
        "acknowledged_count": acknowledged,
        "unacknowledged_count": unacknowledged,
        "affected_districts": {area["_id"]: area["count"] for area in affected_areas if area["_id"]},
    }


@router.get("/by-severity")
def by_severity(days: int = Query(7, ge=1, le=90), db: Database = Depends(get_db)):
    """Get alert breakdown by severity"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    pipeline = [
        {"$match": {"created_at": {"$gte": cutoff_date}}},
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
    ]
    severity_stats = list(db.alerts.aggregate(pipeline))
    
    return {
        "data": {item["_id"]: item["count"] for item in severity_stats if item["_id"]},
        "period_days": days,
    }


@router.get("/active")
def get_active_alerts(db: Database = Depends(get_db)):
    """Get unacknowledged critical and high alerts"""
    active_alerts = list(db.alerts.find({
        "is_acknowledged": False,
        "severity": {"$in": ["critical", "high"]}
    }).sort("created_at", -1).limit(20))
    
    data = []
    for a in active_alerts:
        data.append({
            "id": str(a["_id"]),
            "title": a.get("title"),
            "severity": a.get("severity"),
            "affected_area": a.get("affected_area"),
            "created_at": a.get("created_at").isoformat() if isinstance(a.get("created_at"), datetime) else a.get("created_at"),
        })
        
    return {
        "data": data,
        "count": len(active_alerts),
    }


@router.get("/export/csv")
def export_csv(
    severity: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Database = Depends(get_db),
):
    """Export alerts to CSV"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    filter_query = {"created_at": {"$gte": cutoff_date}}
    
    if severity:
        filter_query["severity"] = severity
    
    alerts = list(db.alerts.find(filter_query).limit(10000))
    
    alert_dicts = []
    for a in alerts:
        alert_dicts.append({
            "title": a.get("title"),
            "severity": a.get("severity"),
            "affected_area": a.get("affected_area"),
            "crime_count_spike": a.get("crime_count_spike"),
            "is_acknowledged": a.get("is_acknowledged", False),
            "created_at": a.get("created_at").isoformat() if isinstance(a.get("created_at"), datetime) else a.get("created_at"),
            "recommendation": a.get("ollama_recommendation", ""),
        })
    
    csv_data = export_alerts_to_csv(alert_dicts)
    
    return {
        "filename": f"alerts_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv",
        "data": csv_data,
    }
