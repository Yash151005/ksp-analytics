"""
KSP Analytics Platform - Main FastAPI Application
"""
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pymongo.database import Database
from bson.objectid import ObjectId
import os
from datetime import datetime, UTC
import logging

from database import init_db, get_db, db_instance
from models import serialize_doc
from routers import crimes, criminals, analytics, alerts, reports, ai, admin
from seed_data import seed_database
from passlib.context import CryptContext

# Suppress MaxListenersExceededWarning from event emitters
logging.getLogger('asyncio').setLevel(logging.WARNING)

# Initialize FastAPI app
app = FastAPI(
    title="KSP Analytics Platform",
    description="AI-Driven Crime Analytics & Visualization for Karnataka State Police",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:8000,https://ksp-analytics.onslate.in").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Add CSP headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "connect-src 'self' http://localhost:5173 http://localhost:8000 https://ksp-analytics.onslate.in https://cdnjs.cloudflare.com; "
        "frame-ancestors 'none';"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

# Authentication endpoints
@app.post("/api/auth/login")
def login(login_data: LoginRequest, db: Database = Depends(get_db)):
    """User login endpoint"""
    user_data = db.users.find_one({"username": login_data.username})
    
    if not user_data or not pwd_context.verify(login_data.password, user_data.get("hashed_password")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user_data.get("is_active"):
        raise HTTPException(status_code=401, detail="User is inactive")
    
    return {
        "message": "Login successful",
        "user": serialize_doc(user_data),
    }


# Audit logging middleware
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log all user actions to audit trail"""
    response = await call_next(request)
    
    # Only log API calls, not static assets
    if request.url.path.startswith("/api/"):
        try:
            audit_log = {
                "user_id": "unknown",
                "action": request.method,
                "resource_type": request.url.path.split("/")[3] if len(request.url.path.split("/")) > 3 else "unknown",
                "ip_address": request.client.host if request.client else None,
                "created_at": datetime.now(UTC)
            }
            db_instance.audit_logs.insert_one(audit_log)
        except Exception:
            pass
    
    return response


# Include routers
app.include_router(crimes.router)
app.include_router(criminals.router)
app.include_router(analytics.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(ai.router)
app.include_router(admin.router)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "KSP Analytics Platform",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting KSP Analytics Platform (MongoDB Version)...")
    
    # Initialize database indexes
    init_db()
    print("✓ Database indexes initialized")
    
    # Check if we need to seed data
    try:
        user_count = db_instance.users.count_documents({})
        if user_count == 0:
            print("📊 Seeding MongoDB database with initial data...")
            seed_database()
        else:
            print(f"✓ Database already has data ({user_count} users)")
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")


@app.get("/api/version")
def get_version():
    """Get API version"""
    return {
        "version": "1.0.0",
        "name": "KSP Analytics Platform",
        "api_version": "v1",
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"\n🌍 Starting server on http://localhost:{port}")
    print(f"📚 API documentation: http://localhost:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=debug,
        log_level="info",
    )
