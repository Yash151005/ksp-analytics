"""
Ollama AI service for KSP Analytics Platform
Handles all LLM interactions with local Ollama instance
"""
import httpx
import json
import hashlib
import time
import os
from typing import Generator, Optional, Dict, Any, List
from datetime import datetime
from database import db_instance

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))  # seconds

# System prompts for different functions
SYSTEM_PROMPTS = {
    "briefing": """You are a senior crime analyst for the Karnataka State Police (KSP). 
Your role is to analyze crime statistics and provide actionable intelligence briefings. 
Keep responses concise, specific, and actionable. Format as 3 bullet points maximum.
Each bullet should be 1-2 sentences. Focus on: trends, hotspots, and immediate concerns.""",

    "hotspots": """You are a geographic crime analyst. Analyze crime location data and identify 
hotspots, dangerous zones, and high-risk areas. Provide risk assessments and polygon descriptions.
Be specific with area names and risk levels. Keep responses concise.""",

    "network": """You are a criminal intelligence analyst specializing in gang structures and 
criminal networks. Analyze criminal association data and provide insights on network topology, 
key players, and gang dynamics. Use professional but accessible language.""",

    "behavioral": """You are a criminal psychologist and behavioral analyst. Profile criminal 
behavior patterns based on crime history. Provide insights on motivation, risk patterns, and 
recommendations for handling. Be professional and evidence-based.""",

    "anomaly": """You are a data analyst specializing in anomaly detection. Explain unusual 
patterns in crime data. Identify causes, impacts, and recommended responses. Be clear and specific.""",

    "forecast": """You are a predictive analyst using historical crime data. Generate a 7-day 
crime forecast for the specified area. Provide risk assessments for each day and recommended 
preventive measures. Base predictions on historical patterns.""",

    "alert": """You are a crime response coordinator. Based on alert data, provide specific 
recommended actions for law enforcement. Include resource deployment, investigation priorities, 
and public safety measures.""",

    "report": """You are a professional report writer for law enforcement agencies. Generate a 
narrative summary of crime data and trends. Write in formal, professional tone suitable for 
senior officials. Include key findings, impacts, and recommendations.""",
}


def hash_input(data: Any) -> str:
    """Generate SHA256 hash of input data"""
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()


def log_ollama_call(
    function_name: str,
    input_data: Any,
    output: str,
    response_time_ms: int,
    error_message: Optional[str] = None,
):
    """Log Ollama call to audit database"""
    try:
        from datetime import UTC
        audit_log = {
            "function_name": function_name,
            "input_hash": hash_input(input_data),
            "output": output[:5000],  # Truncate to 5000 chars
            "response_time_ms": response_time_ms,
            "error_message": error_message,
            "created_at": datetime.now(UTC),
        }
        db_instance.ollama_audit_logs.insert_one(audit_log)
    except Exception as e:
        print(f"Error logging Ollama call: {e}")


def stream_ollama_response(
    function_name: str,
    system_prompt: str,
    user_message: str,
    input_data: Any,
) -> Generator[str, None, None]:
    """
    Stream response from Ollama with error handling
    Yields individual tokens/chunks as they arrive
    """
    start_time = time.time()
    full_response = ""
    error_message = None

    try:
        with httpx.Client(timeout=OLLAMA_TIMEOUT) as client:
            with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": user_message,
                    "system": system_prompt,
                    "stream": True,
                    "temperature": 0.7,
                },
            ) as response:
                if response.status_code != 200:
                    error_message = f"Ollama error: {response.status_code}"
                    yield f"[Error] Unable to connect to Ollama. Please ensure Ollama is running at {OLLAMA_BASE_URL}"
                    log_ollama_call(function_name, input_data, "", int((time.time() - start_time) * 1000), error_message)
                    return

                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "response" in chunk:
                                token = chunk["response"]
                                full_response += token
                                yield token
                        except json.JSONDecodeError:
                            continue

    except httpx.TimeoutException:
        error_message = "Ollama request timeout"
        yield f"\n[Error] Request timed out. Ollama may be overloaded."
    except httpx.ConnectError:
        error_message = "Cannot connect to Ollama"
        yield f"\n[Error] Cannot connect to Ollama at {OLLAMA_BASE_URL}. Is it running?"
    except Exception as e:
        error_message = str(e)
        yield f"\n[Error] Unexpected error: {str(e)}"
    finally:
        response_time_ms = int((time.time() - start_time) * 1000)
        log_ollama_call(function_name, input_data, full_response, response_time_ms, error_message)


def generate_daily_briefing(crime_stats: Dict[str, Any]) -> Generator[str, None, None]:
    """
    Generate 3-bullet daily briefing from crime statistics
    
    Args:
        crime_stats: Dict with keys like total_crimes, top_crime_types, hotspots, etc.
    
    Yields:
        Streaming text of the briefing
    """
    system_prompt = SYSTEM_PROMPTS["briefing"]
    user_message = f"""Analyze this morning's crime statistics and provide 3 key points for the daily briefing:

{json.dumps(crime_stats, indent=2)}

Provide exactly 3 bullet points, each 1-2 sentences. Focus on actionable intelligence."""

    yield from stream_ollama_response("daily_briefing", system_prompt, user_message, crime_stats)


def detect_hotspots(crime_locations: List[Dict[str, Any]]) -> Generator[str, None, None]:
    """
    Detect crime hotspots from GPS coordinates and generate descriptions
    
    Args:
        crime_locations: List of dicts with lat, lng, crime_type, severity
    
    Yields:
        Streaming text with hotspot descriptions
    """
    system_prompt = SYSTEM_PROMPTS["hotspots"]
    user_message = f"""Analyze these crime locations and identify hotspots:

{json.dumps(crime_locations, indent=2)}

Identify 2-3 main hotspot zones. For each, provide:
1. Area name/description
2. Risk level (HIGH/MEDIUM/LOW)
3. Dominant crime type
4. Recommended response"""

    yield from stream_ollama_response("detect_hotspots", system_prompt, user_message, crime_locations)


def analyze_criminal_network(adjacency_data: Dict[str, Any]) -> Generator[str, None, None]:
    """
    Analyze criminal network structure and relationships
    
    Args:
        adjacency_data: Dict with criminal nodes and associations
    
    Yields:
        Streaming text with network analysis
    """
    system_prompt = SYSTEM_PROMPTS["network"]
    user_message = f"""Analyze this criminal network data and provide insights:

{json.dumps(adjacency_data, indent=2)}

Provide analysis on:
1. Network structure (centralized/distributed)
2. Key players and their roles
3. Potential gang clusters
4. Network vulnerabilities to target investigations"""

    yield from stream_ollama_response("analyze_network", system_prompt, user_message, adjacency_data)


def generate_behavioral_profile(criminal_history: Dict[str, Any]) -> Generator[str, None, None]:
    """
    Generate behavioral profile of a criminal
    
    Args:
        criminal_history: Dict with criminal data and crime history
    
    Yields:
        Streaming text with behavioral analysis
    """
    system_prompt = SYSTEM_PROMPTS["behavioral"]
    user_message = f"""Generate a behavioral profile based on this criminal record:

{json.dumps(criminal_history, indent=2)}

Analyze:
1. Crime pattern and specialization
2. Risk assessment
3. Likely motivations
4. Recommendations for interrogation/handling"""

    yield from stream_ollama_response("behavioral_profile", system_prompt, user_message, criminal_history)


def explain_anomaly(anomaly_data: Dict[str, Any]) -> Generator[str, None, None]:
    """
    Explain unusual pattern in crime data
    
    Args:
        anomaly_data: Dict with anomaly metrics and context
    
    Yields:
        Streaming text explaining the anomaly
    """
    system_prompt = SYSTEM_PROMPTS["anomaly"]
    user_message = f"""Explain this anomaly in crime data:

{json.dumps(anomaly_data, indent=2)}

Provide:
1. Description of the anomaly
2. Possible causes
3. Impact assessment
4. Recommended investigation angle"""

    yield from stream_ollama_response("explain_anomaly", system_prompt, user_message, anomaly_data)


def forecast_crime_trend(historical_data: List[Dict[str, Any]]) -> Generator[str, None, None]:
    """
    Generate 7-day crime forecast based on historical data
    
    Args:
        historical_data: List of daily crime counts and patterns
    
    Yields:
        Streaming text with forecast narrative
    """
    system_prompt = SYSTEM_PROMPTS["forecast"]
    user_message = f"""Generate a 7-day crime forecast based on this historical data:

{json.dumps(historical_data, indent=2)}

Provide day-by-day forecast including:
1. Predicted crime levels (Low/Medium/High)
2. Expected crime types
3. Risk areas
4. Resource recommendations"""

    yield from stream_ollama_response("forecast_crime", system_prompt, user_message, historical_data)


def generate_alert_recommendation(alert_data: Dict[str, Any]) -> Generator[str, None, None]:
    """
    Generate recommended response actions for a crime alert
    
    Args:
        alert_data: Dict with alert details and context
    
    Yields:
        Streaming text with recommendations
    """
    system_prompt = SYSTEM_PROMPTS["alert"]
    user_message = f"""Generate response recommendations for this alert:

{json.dumps(alert_data, indent=2)}

Provide specific recommendations for:
1. Immediate response actions
2. Resource allocation
3. Investigation priorities
4. Public safety measures"""

    yield from stream_ollama_response("alert_recommendation", system_prompt, user_message, alert_data)


def generate_report_narrative(report_data: Dict[str, Any]) -> Generator[str, None, None]:
    """
    Generate professional narrative summary for a report
    
    Args:
        report_data: Dict with report metrics and data
    
    Yields:
        Streaming text with report narrative
    """
    system_prompt = SYSTEM_PROMPTS["report"]
    user_message = f"""Write a professional narrative summary for this crime report:

{json.dumps(report_data, indent=2)}

Generate a formal paragraph (150-250 words) covering:
1. Period overview
2. Key statistics and trends
3. Geographic focus areas
4. Notable incidents or patterns
5. Recommendations"""

    yield from stream_ollama_response("report_narrative", system_prompt, user_message, report_data)
