"""
Criminals router for KSP Analytics Platform MongoDB
Handles all criminal record endpoints
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from pymongo.database import Database
from bson.objectid import ObjectId
from typing import List, Optional
from database import get_db
from models import serialize_docs, serialize_doc
from services.export_service import export_criminals_to_csv
from datetime import datetime, UTC
import re

router = APIRouter(prefix="/api/criminals", tags=["criminals"])


@router.get("/")
def list_criminals(
    status: Optional[str] = Query(None),
    min_risk_score: Optional[float] = Query(None, ge=0, le=100),
    max_risk_score: Optional[float] = Query(None, ge=0, le=100),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Database = Depends(get_db),
):
    """List criminals with filtering and pagination"""
    filter_query = {}
    
    if status:
        filter_query["status"] = status
    
    risk_filter = {}
    if min_risk_score is not None:
        risk_filter["$gte"] = min_risk_score
    if max_risk_score is not None:
        risk_filter["$lte"] = max_risk_score
    if risk_filter:
        filter_query["risk_score"] = risk_filter
        
    if search:
        search_regex = re.compile(f".*{search}.*", re.IGNORECASE)
        filter_query["$or"] = [
            {"name": search_regex},
            {"alias": search_regex},
            {"aadhaar_hash": search_regex}
        ]
    
    total = db.criminals.count_documents(filter_query)
    criminals = list(db.criminals.find(filter_query).sort("risk_score", -1).skip(offset).limit(limit))
    
    data = []
    for c in criminals:
        assoc = c.get("associated_criminal_ids", [])
        data.append({
            "id": str(c["_id"]),
            "name": c.get("name"),
            "alias": c.get("alias"),
            "age": c.get("age"),
            "gender": c.get("gender"),
            "status": c.get("status"),
            "risk_score": c.get("risk_score"),
            "crime_count": len(c.get("crime_history", [])),
            "associates_count": len(assoc),
            "last_known_location": c.get("last_known_location"),
        })
    
    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{criminal_id}")
def get_criminal(criminal_id: str, db: Database = Depends(get_db)):
    """Get criminal details by ID"""
    try:
        obj_id = ObjectId(criminal_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid criminal ID format")
        
    criminal = db.criminals.find_one({"_id": obj_id})
    if not criminal:
        raise HTTPException(status_code=404, detail="Criminal not found")
        
    # Get associates details
    associate_ids = criminal.get("associated_criminal_ids", [])
    assoc_obj_ids = []
    for a_id in associate_ids:
        try:
            assoc_obj_ids.append(ObjectId(a_id))
        except:
            pass
            
    associates = list(db.criminals.find({"_id": {"$in": assoc_obj_ids}}))
    
    known_associates = [
        {
            "id": str(a["_id"]),
            "name": a.get("name"),
            "alias": a.get("alias"),
            "risk_score": a.get("risk_score"),
            "status": a.get("status"),
        }
        for a in associates
    ]
    
    result = serialize_doc(criminal)
    result["crime_count"] = len(result.get("crime_history", []))
    result["known_associates"] = known_associates
    
    if "created_at" in result and isinstance(result["created_at"], datetime):
        result["created_at"] = result["created_at"].isoformat()
    if "updated_at" in result and isinstance(result["updated_at"], datetime):
        result["updated_at"] = result["updated_at"].isoformat()
        
    return result


@router.get("/{criminal_id}/associates")
def get_associates(criminal_id: str, db: Database = Depends(get_db)):
    """Get known associates of a criminal"""
    try:
        obj_id = ObjectId(criminal_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid criminal ID format")
        
    criminal = db.criminals.find_one({"_id": obj_id})
    if not criminal:
        raise HTTPException(status_code=404, detail="Criminal not found")
    
    associate_ids = criminal.get("associated_criminal_ids", [])
    assoc_obj_ids = []
    for a_id in associate_ids:
        try:
            assoc_obj_ids.append(ObjectId(a_id))
        except:
            pass
            
    associates = list(db.criminals.find({"_id": {"$in": assoc_obj_ids}}))
    
    return {
        "criminal_id": criminal_id,
        "criminal_name": criminal.get("name"),
        "associates": [
            {
                "id": str(a["_id"]),
                "name": a.get("name"),
                "alias": a.get("alias"),
                "age": a.get("age"),
                "gender": a.get("gender"),
                "risk_score": a.get("risk_score"),
                "status": a.get("status"),
                "crime_count": len(a.get("crime_history", [])),
            }
            for a in associates
        ],
    }


@router.get("/network/data")
def get_network(db: Database = Depends(get_db)):
    """
    Get network graph data for D3.js visualization
    Returns nodes and links for criminal association network, including vehicles and bank accounts
    """
    criminals = list(db.criminals.find({"risk_score": {"$gte": 20}}).limit(100))
    
    nodes = []
    links = []
    processed_associations = set()
    
    criminal_dict = {str(c["_id"]): c for c in criminals}
    criminal_ids = list(criminal_dict.keys())
    
    # Fetch associated vehicles and bank accounts
    vehicles = list(db.vehicles.find({"criminal_id": {"$in": criminal_ids}}))
    bank_accounts = list(db.bank_accounts.find({"criminal_id": {"$in": criminal_ids}}))
    
    for c in criminals:
        c_id = str(c["_id"])
        nodes.append({
            "id": c_id,
            "type": "criminal",
            "name": c.get("name"),
            "alias": c.get("alias"),
            "risk_score": c.get("risk_score"),
            "status": c.get("status"),
            "crime_count": len(c.get("crime_history", [])),
        })
        
        for a_id in c.get("associated_criminal_ids", []):
            if a_id in criminal_dict:
                link_id = tuple(sorted([c_id, a_id]))
                if link_id not in processed_associations:
                    processed_associations.add(link_id)
                    links.append({
                        "source": c_id,
                        "target": a_id,
                        "strength": min(10, len(c.get("crime_history", []))) / 10,
                        "type": "association"
                    })
                    
    for v in vehicles:
        v_id = str(v["_id"])
        c_id = v["criminal_id"]
        nodes.append({
            "id": v_id,
            "type": "vehicle",
            "name": v.get("license_plate"),
            "make_model": v.get("make_model"),
            "color": v.get("color"),
            "risk_score": 10, # default visual size
        })
        links.append({
            "source": c_id,
            "target": v_id,
            "strength": 0.5,
            "type": "ownership"
        })
        
    for b in bank_accounts:
        b_id = str(b["_id"])
        c_id = b["criminal_id"]
        nodes.append({
            "id": b_id,
            "type": "bank",
            "name": b.get("bank_name"),
            "account_number": b.get("account_number"),
            "balance": b.get("balance"),
            "risk_score": 10, # default visual size
        })
        links.append({
            "source": c_id,
            "target": b_id,
            "strength": 0.5,
            "type": "ownership"
        })
    
    return {
        "nodes": nodes,
        "links": links,
    }


@router.get("/stats/summary")
def get_stats(db: Database = Depends(get_db)):
    """Get criminal statistics"""
    total_criminals = db.criminals.count_documents({})
    active_criminals = db.criminals.count_documents({"status": "active"})
    absconding = db.criminals.count_documents({"status": "absconding"})
    arrested = db.criminals.count_documents({"status": "arrested"})
    
    high_risk = db.criminals.count_documents({"risk_score": {"$gte": 70}})
    
    pipeline = [{"$group": {"_id": None, "avg_score": {"$avg": "$risk_score"}}}]
    result = list(db.criminals.aggregate(pipeline))
    avg_risk_score = result[0]["avg_score"] if result else 0
    
    return {
        "total_criminals": total_criminals,
        "active_criminals": active_criminals,
        "absconding_count": absconding,
        "arrested_count": arrested,
        "high_risk_count": high_risk,
        "average_risk_score": round(avg_risk_score, 2),
    }


@router.get("/high-risk")
def get_high_risk_criminals(db: Database = Depends(get_db)):
    """Get list of high-risk criminals (risk score >= 70)"""
    from services.analytics_service import get_high_risk_criminals
    return get_high_risk_criminals(min_risk_score=70)


@router.get("/export/csv")
def export_csv(
    status: Optional[str] = Query(None),
    db: Database = Depends(get_db),
):
    """Export criminals to CSV"""
    filter_query = {}
    if status:
        filter_query["status"] = status
        
    criminals = list(db.criminals.find(filter_query).limit(10000))
    csv_data = export_criminals_to_csv(criminals)
    
    return {
        "filename": f"criminals_export_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv",
        "data": csv_data,
    }
