"""
KSP Analytics Platform - Main FastAPI Application
"""
import os
import sys
# Insert local vendor directory to sys.path on Catalyst (Linux) or when specified by Catalyst port
if os.name != 'nt' or os.getenv("X_ZOHO_CATALYST_LISTEN_PORT"):
    lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
    if lib_path not in sys.path:
        sys.path.insert(0, lib_path)

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pymongo.database import Database
from bson.objectid import ObjectId
import os
from datetime import datetime, timezone
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

# Add CORS middleware only for local development. Catalyst Advanced API Gateway automatically handles CORS in production.
if not os.getenv("X_ZOHO_CATALYST_LISTEN_PORT"):
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https://.*\.onslate\.in|https://.*\.catalystserverless\.in|https://.*\.catalystappsail\.in|http://localhost:.*",
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
        "connect-src 'self' http://localhost:5173 http://localhost:8000 https://ksp-analytics.onslate.in https://*.catalystappsail.in https://ksp-analytics-api-50043270677.development.catalystappsail.in https://cdnjs.cloudflare.com; "
        "frame-ancestors 'none';"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Force HTTPS scheme in Catalyst AppSail environment to prevent HTTP 307 redirects
@app.middleware("http")
async def force_https_scheme(request: Request, call_next):
    if os.getenv("X_ZOHO_CATALYST_LISTEN_PORT"):
        request.scope["scheme"] = "https"
    return await call_next(request)


# Configuration
pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

# Authentication endpoints
@app.post("/api/auth/login")
def login(login_data: LoginRequest, db: Database = Depends(get_db)):
    """User login endpoint"""
    try:
        user_data = db.users.find_one({"$or": [{"username": login_data.username}, {"email": login_data.username}]})
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        is_match = pwd_context.verify(login_data.password, user_data.get("hashed_password"))
        if not is_match:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user_data.get("is_active"):
            raise HTTPException(status_code=401, detail="User is inactive")
        
        return {
            "message": "Login successful",
            "user": serialize_doc(user_data),
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Exception during login: {tb}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": tb}
        )


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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


from fastapi import BackgroundTasks

@app.on_event("startup")
def startup_event():
    """Initialize app on startup without blocking the main thread"""
    print("Starting KSP Analytics Platform (MongoDB Version)...")
    print("Database initialization deferred to background or first request to prevent boot hangs.")


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
    
    try:
        port_str = os.getenv("X_ZOHO_CATALYST_LISTEN_PORT", os.getenv("PORT", "8000"))
        if not port_str or port_str.strip() == "":
            port_str = "8000"
        port = int(port_str)
    except ValueError:
        port = 8000
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"\nStarting server on http://localhost:{port}")
    print(f"API documentation: http://localhost:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=debug,
        log_level="info",
    )
# Force Catalyst deploy
