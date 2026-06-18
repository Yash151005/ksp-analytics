"""
Admin router for KSP Analytics Platform MongoDB
Handles user management, audit logs, and system administration
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database
from bson.objectid import ObjectId
from datetime import datetime, timedelta, UTC
from typing import Optional
from database import get_db
from models import serialize_docs, serialize_doc
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Role permissions matrix
ROLE_PERMISSIONS = {
    "admin": {
        "view_crimes": True,
        "view_criminals": True,
        "view_analytics": True,
        "view_reports": True,
        "create_reports": True,
        "export_data": True,
        "manage_users": True,
        "view_audit_logs": True,
        "manage_alerts": True,
    },
    "analyst": {
        "view_crimes": True,
        "view_criminals": True,
        "view_analytics": True,
        "view_reports": True,
        "create_reports": True,
        "export_data": True,
        "manage_users": False,
        "view_audit_logs": False,
        "manage_alerts": False,
    },
    "investigator": {
        "view_crimes": True,
        "view_criminals": True,
        "view_analytics": False,
        "view_reports": False,
        "create_reports": False,
        "export_data": True,
        "manage_users": False,
        "view_audit_logs": False,
        "manage_alerts": True,
    },
    "viewer": {
        "view_crimes": True,
        "view_criminals": False,
        "view_analytics": False,
        "view_reports": False,
        "create_reports": False,
        "export_data": False,
        "manage_users": False,
        "view_audit_logs": False,
        "manage_alerts": False,
    },
}


@router.get("/users")
def list_users(
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Database = Depends(get_db),
):
    """List all users with filtering"""
    filter_query = {}
    
    if role:
        filter_query["role"] = role
    
    if is_active is not None:
        filter_query["is_active"] = is_active
    
    total = db.users.count_documents(filter_query)
    users = list(db.users.find(filter_query).sort("created_at", -1).skip(offset).limit(limit))
    
    data = []
    for u in users:
        data.append({
            "id": str(u["_id"]),
            "username": u.get("username"),
            "email": u.get("email"),
            "full_name": u.get("full_name"),
            "role": u.get("role"),
            "is_active": u.get("is_active", True),
            "created_at": u.get("created_at").isoformat() if isinstance(u.get("created_at"), datetime) else u.get("created_at"),
            "updated_at": u.get("updated_at").isoformat() if isinstance(u.get("updated_at"), datetime) else u.get("updated_at"),
        })
    
    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/users")
def create_user(
    username: str,
    email: str,
    password: str,
    full_name: str,
    role: str = "viewer",
    db: Database = Depends(get_db),
):
    """Create a new user"""
    # Check if user already exists
    existing_user = db.users.find_one({"$or": [{"username": username}, {"email": email}]})
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Validate role
    if role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    
    now = datetime.now(UTC)
    user_doc = {
        "username": username,
        "email": email,
        "hashed_password": pwd_context.hash(password),
        "full_name": full_name,
        "role": role,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    
    result = db.users.insert_one(user_doc)
    
    return {
        "id": str(result.inserted_id),
        "username": username,
        "email": email,
        "full_name": full_name,
        "role": role,
        "is_active": True,
        "created_at": now.isoformat(),
    }


@router.get("/users/{user_id}")
def get_user(user_id: str, db: Database = Depends(get_db)):
    """Get user details"""
    try:
        obj_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
        
    user = db.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    result = serialize_doc(user)
    result.pop("hashed_password", None)
    
    if "created_at" in result and isinstance(result["created_at"], datetime):
        result["created_at"] = result["created_at"].isoformat()
    if "updated_at" in result and isinstance(result["updated_at"], datetime):
        result["updated_at"] = result["updated_at"].isoformat()
        
    return result


@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Database = Depends(get_db),
):
    """Update user details"""
    try:
        obj_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
        
    user = db.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {"updated_at": datetime.now(UTC)}
    
    if email:
        update_data["email"] = email
    if full_name:
        update_data["full_name"] = full_name
    if role:
        if role not in ROLE_PERMISSIONS:
            raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
        update_data["role"] = role
    if is_active is not None:
        update_data["is_active"] = is_active
    
    db.users.update_one({"_id": obj_id}, {"$set": update_data})
    
    updated_user = db.users.find_one({"_id": obj_id})
    result = serialize_doc(updated_user)
    result.pop("hashed_password", None)
    
    if "created_at" in result and isinstance(result["created_at"], datetime):
        result["created_at"] = result["created_at"].isoformat()
    if "updated_at" in result and isinstance(result["updated_at"], datetime):
        result["updated_at"] = result["updated_at"].isoformat()
        
    return result


@router.delete("/users/{user_id}")
def deactivate_user(user_id: str, db: Database = Depends(get_db)):
    """Deactivate a user (soft delete)"""
    try:
        obj_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
        
    result = db.users.update_one(
        {"_id": obj_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(UTC)}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deactivated", "user_id": user_id}


@router.get("/permissions")
def get_permissions_matrix():
    """Get role permissions matrix"""
    return {
        "roles": list(ROLE_PERMISSIONS.keys()),
        "permissions_matrix": ROLE_PERMISSIONS,
    }


@router.get("/audit-logs")
def list_audit_logs(
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Database = Depends(get_db),
):
    """List audit logs"""
    cutoff_date = datetime.now(UTC) - timedelta(days=days)
    
    filter_query = {"created_at": {"$gte": cutoff_date}}
    
    if user_id:
        filter_query["user_id"] = user_id
    
    if action:
        filter_query["action"] = action
    
    if resource_type:
        filter_query["resource_type"] = resource_type
    
    total = db.audit_logs.count_documents(filter_query)
    logs = list(db.audit_logs.find(filter_query).sort("created_at", -1).skip(offset).limit(limit))
    
    data = []
    for log in logs:
        data.append({
            "id": str(log["_id"]),
            "user_id": log.get("user_id"),
            "action": log.get("action"),
            "resource_type": log.get("resource_type"),
            "resource_id": log.get("resource_id"),
            "ip_address": log.get("ip_address"),
            "created_at": log.get("created_at").isoformat() if isinstance(log.get("created_at"), datetime) else log.get("created_at"),
        })
    
    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/audit-logs/stats")
def audit_stats(days: int = Query(30, ge=1, le=365), db: Database = Depends(get_db)):
    """Get audit log statistics"""
    cutoff_date = datetime.now(UTC) - timedelta(days=days)
    
    total_actions = db.audit_logs.count_documents({"created_at": {"$gte": cutoff_date}})
    
    pipeline_action = [
        {"$match": {"created_at": {"$gte": cutoff_date}}},
        {"$group": {"_id": "$action", "count": {"$sum": 1}}}
    ]
    action_stats = {item["_id"]: item["count"] for item in db.audit_logs.aggregate(pipeline_action) if item["_id"]}
    
    pipeline_resource = [
        {"$match": {"created_at": {"$gte": cutoff_date}}},
        {"$group": {"_id": "$resource_type", "count": {"$sum": 1}}}
    ]
    resource_stats = {item["_id"]: item["count"] for item in db.audit_logs.aggregate(pipeline_resource) if item["_id"]}
    
    pipeline_user = [
        {"$match": {"created_at": {"$gte": cutoff_date}}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    user_stats = {item["_id"]: item["count"] for item in db.audit_logs.aggregate(pipeline_user) if item["_id"]}
    
    return {
        "total_actions": total_actions,
        "period_days": days,
        "by_action": action_stats,
        "by_resource_type": resource_stats,
        "top_users": user_stats,
    }


@router.get("/system-health")
def get_system_health(db: Database = Depends(get_db)):
    """Get system health and status information"""
    try:
        # Check database
        db.users.find_one({})
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check Ollama
    try:
        import httpx
        import asyncio
        
        async def check_ollama():
            async with httpx.AsyncClient(timeout=5) as client:
                try:
                    response = await client.get("http://localhost:11434/api/tags")
                    return response.status_code == 200
                except:
                    return False
        
        loop = asyncio.new_event_loop()
        ollama_running = loop.run_until_complete(check_ollama())
        ollama_status = "ready" if ollama_running else "unavailable"
    except Exception as e:
        ollama_status = f"error: {str(e)}"
    
    # Get crime data counts
    try:
        crime_count = db.crimes.count_documents({})
        criminal_count = db.criminals.count_documents({})
    except:
        crime_count = 0
        criminal_count = 0
    
    return {
        "database": {
            "status": db_status,
            "crime_records": crime_count,
            "criminal_records": criminal_count,
        },
        "ollama": {
            "status": ollama_status,
            "model": "llama3",
            "url": "http://localhost:11434",
        },
        "timestamp": datetime.now(UTC).isoformat(),
    }
