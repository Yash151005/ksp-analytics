"""
AI router for KSP Analytics Platform MongoDB
Handles Ollama LLM streaming and AI endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pymongo.database import Database
from bson.objectid import ObjectId
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import json
import asyncio
from database import get_db
from models import serialize_docs, serialize_doc
from services.ollama_service import (
    generate_daily_briefing,
    detect_hotspots,
    analyze_criminal_network,
    generate_behavioral_profile,
    explain_anomaly,
    forecast_crime_trend,
    generate_alert_recommendation,
    generate_report_narrative,
)
from services.analytics_service import (
    get_crime_summary,
    get_high_risk_zones,
    get_temporal_heatmap,
    get_anomalies,
    get_crime_trend,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


async def stream_generator(generator, timeout=30):
    """
    Convert sync generator to async generator with proper SSE formatting.
    Includes timeout protection and proper stream termination.
    """
    try:
        for chunk in generator:
            # Yield formatted SSE message
            yield f"data: {json.dumps({'content': chunk})}\n\n"
            await asyncio.sleep(0.01)  # Small delay to allow other tasks
        
        # Send completion marker
        yield "data: [DONE]\n\n"
    except GeneratorExit:
        # Client disconnected, clean up gracefully
        pass
    except Exception as e:
        # Send error as final message
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"


@router.post("/briefing")
async def generate_briefing(db: Database = Depends(get_db)):
    """
    Generate daily AI briefing from crime statistics
    Returns Server-Sent Events stream
    """
    try:
        # Get current crime statistics
        crime_stats = get_crime_summary(days=1)
        crime_stats["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Generate briefing with Ollama
        generator = generate_daily_briefing(crime_stats)
        
        return StreamingResponse(
            stream_generator(generator),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        return StreamingResponse(
            (f"data: {json.dumps({'error': str(e)})}\n\ndata: [DONE]\n\n" for _ in [1]),
            media_type="text/event-stream",
            status_code=500
        )


@router.post("/analyze-network")
async def analyze_network(db: Database = Depends(get_db)):
    """
    Analyze criminal network structure with Ollama
    Returns Server-Sent Events stream
    """
    try:
        # Get network data
        criminals = list(db.criminals.find({"risk_score": {"$gte": 20}}).limit(50))
        
        if not criminals:
            async def empty_response():
                yield "data: {\"content\": \"No criminals with sufficient risk score found.\"}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(empty_response(), media_type="text/event-stream")
        
        adjacency_data = {
            "criminals": [
                {
                    "id": str(c["_id"]),
                    "name": c.get("name"),
                    "risk_score": c.get("risk_score"),
                    "crime_count": len(c.get("crime_history", [])),
                    "status": c.get("status"),
                }
                for c in criminals
            ],
            "associations": [
                {
                    "source_id": str(c["_id"]),
                    "targets": [str(a) for a in c.get("associated_criminal_ids", [])],
                }
                for c in criminals if c.get("associated_criminal_ids")
            ],
        }
        
        generator = analyze_criminal_network(adjacency_data)
        
        return StreamingResponse(
            stream_generator(generator),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        return StreamingResponse(
            (f"data: {json.dumps({'error': str(e)})}\n\ndata: [DONE]\n\n" for _ in [1]),
            media_type="text/event-stream",
            status_code=500
        )


@router.post("/profile/{criminal_id}")
async def generate_profile(criminal_id: str, db: Database = Depends(get_db)):
    """
    Generate behavioral profile for a criminal
    Returns Server-Sent Events stream
    """
    try:
        try:
            obj_id = ObjectId(criminal_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid criminal ID format")
            
        criminal = db.criminals.find_one({"_id": obj_id})
        if not criminal:
            async def not_found():
                yield "data: {\"error\": \"Criminal not found\"}\n\ndata: [DONE]\n\n"
            return StreamingResponse(not_found(), media_type="text/event-stream", status_code=404)
        
        criminal_history = {
            "name": criminal.get("name"),
            "age": criminal.get("age"),
            "gender": criminal.get("gender"),
            "status": criminal.get("status"),
            "risk_score": criminal.get("risk_score"),
            "crime_count": len(criminal.get("crime_history", [])),
            "crimes": criminal.get("crime_history", []),
            "associates_count": len(criminal.get("associated_criminal_ids", [])),
        }
        
        generator = generate_behavioral_profile(criminal_history)
        
        return StreamingResponse(
            stream_generator(generator),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        return StreamingResponse(
            (f"data: {json.dumps({'error': str(e)})}\n\ndata: [DONE]\n\n" for _ in [1]),
            media_type="text/event-stream",
            status_code=500
        )


@router.post("/hotspots")
async def detect_hotspots_ai(db: Database = Depends(get_db)):
    """
    Detect crime hotspots with Ollama analysis
    Returns Server-Sent Events stream
    """
    try:
        # Get crime location data
        crimes = list(db.crimes.find({
            "latitude": {"$ne": None},
            "longitude": {"$ne": None}
        }).limit(200))
        
        if not crimes:
            async def no_crimes():
                yield "data: {\"content\": \"No crime location data available.\"}\n\ndata: [DONE]\n\n"
            return StreamingResponse(no_crimes(), media_type="text/event-stream")
        
        crime_locations = [
            {
                "id": str(c["_id"]),
                "crime_id": c.get("crime_id"),
                "latitude": c.get("latitude"),
                "longitude": c.get("longitude"),
                "crime_type": c.get("type"),
                "severity": c.get("severity"),
                "district": c.get("district"),
                "date": c.get("date").isoformat() if isinstance(c.get("date"), datetime) else str(c.get("date")),
            }
            for c in crimes
        ]
        
        generator = detect_hotspots(crime_locations)
        
        return StreamingResponse(
            stream_generator(generator),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        return StreamingResponse(
            (f"data: {json.dumps({'error': str(e)})}\n\ndata: [DONE]\n\n" for _ in [1]),
            media_type="text/event-stream",
            status_code=500
        )


@router.post("/forecast")
async def forecast_trends(days: int = 7, db: Database = Depends(get_db)):
    """
    Generate 7-day crime forecast with Ollama
    Returns Server-Sent Events stream
    """
    try:
        # Get historical trend data
        trend_data = get_crime_trend(months=3)
        
        if not trend_data:
            async def no_trend():
                yield "data: {\"content\": \"Insufficient historical data for forecast.\"}\n\ndata: [DONE]\n\n"
            return StreamingResponse(no_trend(), media_type="text/event-stream")
        
        # Prepare forecast input
        historical_data = [
            {
                "month": item["date"],
                "crime_count": item["count"],
                "avg_severity": item["severity_avg"],
            }
            for item in trend_data
        ]
        
        generator = forecast_crime_trend(historical_data)
        
        return StreamingResponse(
            stream_generator(generator),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        return StreamingResponse(
            (f"data: {json.dumps({'error': str(e)})}\n\ndata: [DONE]\n\n" for _ in [1]),
            media_type="text/event-stream",
            status_code=500
        )


@router.post("/anomaly-explanation")
async def explain_anomaly_ai(anomaly_data: Dict[str, Any], db: Database = Depends(get_db)):
    """
    Explain an anomaly in crime data with Ollama
    Returns Server-Sent Events stream
    """
    try:
        generator = explain_anomaly(anomaly_data)
        
        return StreamingResponse(
            stream_generator(generator),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        return StreamingResponse(
            (f"data: {json.dumps({'error': str(e)})}\n\ndata: [DONE]\n\n" for _ in [1]),
            media_type="text/event-stream",
            status_code=500
        )


@router.post("/alert-recommendation")
async def get_alert_recommendation_ai(alert_data: Dict[str, Any], db: Database = Depends(get_db)):
    """
    Generate recommended response for an alert
    Returns Server-Sent Events stream
    """
    try:
        generator = generate_alert_recommendation(alert_data)
        
        return StreamingResponse(
            stream_generator(generator),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        return StreamingResponse(
            (f"data: {json.dumps({'error': str(e)})}\n\ndata: [DONE]\n\n" for _ in [1]),
            media_type="text/event-stream",
            status_code=500
        )


@router.post("/report-narrative")
async def generate_report_summary(report_data: Dict[str, Any], db: Database = Depends(get_db)):
    """
    Generate professional narrative for a report
    Returns Server-Sent Events stream
    """
    try:
        generator = generate_report_narrative(report_data)
        
        return StreamingResponse(
            stream_generator(generator),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        return StreamingResponse(
            (f"data: {json.dumps({'error': str(e)})}\n\ndata: [DONE]\n\n" for _ in [1]),
            media_type="text/event-stream",
            status_code=500
        )


@router.get("/status")
def get_ollama_status():
    """Check LLM service status (local Ollama or hosted providers)"""
    try:
        import httpx
        import asyncio
        import os
        
        has_gemini = bool(os.getenv("GEMINI_API_KEY"))
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        
        async def check():
            async with httpx.AsyncClient(timeout=2) as client:
                try:
                    response = await client.get("http://localhost:11434/api/tags")
                    return response.status_code == 200
                except:
                    return False
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        ollama_running = loop.run_until_complete(check())
        
        is_running = has_gemini or has_openai or ollama_running
        active_model = "gemini-1.5-flash" if has_gemini else ("gpt-4o-mini" if has_openai else "llama3")
        provider = "gemini" if has_gemini else ("openai" if has_openai else ("ollama" if ollama_running else "simulated"))
        
        return {
            "ollama_running": is_running,
            "model": active_model,
            "status": "ready" if is_running else "unavailable",
            "provider": provider,
        }
    except Exception as e:
        return {
            "ollama_running": False,
            "model": "llama3",
            "status": "unavailable",
            "error": str(e),
        }
