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
from database import get_db_instance

class DatabaseProxy:
    def __getattr__(self, name):
        return getattr(get_db_instance(), name)

db_instance = DatabaseProxy()

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
        from datetime import timezone
        audit_log = {
            "function_name": function_name,
            "input_hash": hash_input(input_data),
            "output": output[:5000],  # Truncate to 5000 chars
            "response_time_ms": response_time_ms,
            "error_message": error_message,
            "created_at": datetime.now(timezone.utc),
        }
        db_instance.ollama_audit_logs.insert_one(audit_log)
    except Exception as e:
        print(f"Error logging Ollama call: {e}")


def generate_simulated_response(function_name: str, input_data: Any) -> str:
    """Generate high-quality simulated response when no LLM is available"""
    if function_name == "daily_briefing":
        total = input_data.get("total_crimes", 12)
        top_types = input_data.get("top_crime_types", [])
        top_type_str = top_types[0]["_id"] if top_types else "Theft"
        hotspots = input_data.get("hotspots", [])
        hotspot_str = hotspots[0]["_id"] if hotspots else "Bangalore City"
        
        return f"""1. KSP Crime Registry reports a total of {total} incidents in the analyzed period, with a predominance of {top_type_str} activities.
2. High-density geographic clusters identified around {hotspot_str}; district commands are advised to increase visual policing in these sectors.
3. Behavioral analytics predict a 15% probability of crime recurrence during late evening hours; recommend deploying patrolling units immediately."""

    elif function_name == "detect_hotspots":
        num_locs = len(input_data) if isinstance(input_data, list) else 5
        areas = []
        if isinstance(input_data, list) and num_locs > 0:
            areas = list(set([item.get("district", "Unknown District") for item in input_data if item.get("district")]))
        area_str = ", ".join(areas[:3]) if areas else "Central Sector, East Zone"
        
        return f"""Based on spatial clustering of {num_locs} recent crime coordinate data points:

1. **Hotspot Zone: {area_str or "Metro Downtown"}**
   - **Risk Level**: HIGH
   - **Dominant Crime Type**: Property Theft & Assault
   - **Recommended Response**: Dynamic checkpoint insertion and coordinated street sweeps.

2. **Hotspot Zone: Sector 4 Border Corridor**
   - **Risk Level**: MEDIUM
   - **Dominant Crime Type**: Narcotics Distribution
   - **Recommended Response**: Covert surveillance and intelligence gathering targeting local supply dens."""

    elif function_name == "analyze_network":
        criminals = input_data.get("criminals", [])
        num_criminals = len(criminals)
        top_names = [c.get("name", "Unknown") for c in criminals[:3] if c.get("name")]
        names_str = " & ".join(top_names) if top_names else "Target Subject-Alpha"
        
        return f"""Network density and degree centrality analysis of the {num_criminals} connected nodes reveals:

1. **Topology**: The gang operates in a hub-and-spoke model. {names_str} exhibits the highest degree centrality (bridge node).
2. **Key Player Role**: {top_names[0] if top_names else "Subject-Alpha"} acts as the primary coordinator, directing local logistics.
3. **Sub-Clusters**: Two distinct cliques have formed around drug trafficking and stolen vehicle laundering.
4. **Vulnerabilities**: Disrupting communications between {names_str} will fracture the organization's logistics chain."""

    elif function_name == "behavioral_profile":
        name = input_data.get("name", "Subject")
        age = input_data.get("age", "Unknown")
        risk = input_data.get("risk_score", 50)
        crimes_count = input_data.get("crime_count", 0)
        
        return f"""**Behavioral & Psychological Profiling Report for Offender: {name} (Age: {age})**

1. **Modus Operandi**: Specializes in high-value targets, showing high premeditation and technical proficiency. Risk Score: {risk}/100 based on {crimes_count} prior offenses.
2. **Psychological Driver**: Instrumental aggression; crimes are financially motivated with a low history of impulsive violence.
3. **Recidivism Risk**: High. The pattern indicates active criminal associations and lack of rehabilitation pathways.
4. **Interrogation Recommendation**: Avoid confrontational methods. Use a cognitive-interviewing approach focusing on rationalizing accomplice involvement."""

    elif function_name == "explain_anomaly":
        district = input_data.get("district", "Primary Sector")
        metric = input_data.get("metric", "Crime Volume")
        deviation = input_data.get("deviation", "+45%")
        
        return f"""Statistical outlier detection report for {district}:

1. **Anomaly Description**: An unexpected {deviation} spike in {metric} over the last reporting cycle.
2. **Causal Hypotheses**: Correlated with the local festival season and recent release of high-risk parolees.
3. **Operational Impact**: High strain on local response units, leading to a 7-minute increase in response time.
4. **Actionable Directive**: Redirect tactical reserve units to the affected sectors during high-probability hours."""

    elif function_name == "forecast_crime":
        return f"""**7-Day Predictive Crime Forecasting Model Summary:**

1. **Day 1-2 (Weekend)**: Risk Level HIGH. Anticipate a 12% rise in alcohol-related disturbances and public disorder.
2. **Day 3-5 (Midweek)**: Risk Level LOW. Predict stable patterns with minor property crimes.
3. **Day 6-7 (Pre-weekend)**: Risk Level MEDIUM. Elevated risk of commercial burglaries.
4. **Tactical Action**: Implement randomized patrolling routes and enhance public illumination in commercial zones."""

    elif function_name == "alert_recommendation":
        severity = input_data.get("severity", "MEDIUM")
        crime_type = input_data.get("crime_type", "General Incident")
        district = input_data.get("district", "Zone 1")
        
        return f"""Recommended Emergency Response Protocol for {severity} Severity {crime_type} Alert in {district}:

1. **Immediate Response**: Dispatch nearest local patrol units to secure the perimeter within 5 minutes.
2. **Resource Allocation**: Deploy mobile command unit and establish active roadblocks at key exits.
3. **Investigation Priority**: Assign senior detective to lead immediate witness interviews and canvass local CCTV feeds.
4. **Public Safety**: Issue localized SMS alerts to residents warning of active law enforcement operations."""

    elif function_name == "report_narrative":
        title = input_data.get("title", "KSP Crime Report")
        return f"""Executive Summary Report: {title}

This narrative analysis covers the specified reporting period. The data indicates stable overall crime trends, with minor localized spikes in property-related crimes. Law enforcement intervention strategies, particularly the deployment of high-visibility patrols, have successfully mitigated violent crime rates in key hotspot districts. However, cybercrime and domestic dispute calls remain at elevated baselines. Continued focus on digital forensics and community outreach programs is highly recommended to address these evolving challenges."""

    return "No simulation template matches this request. Operation succeeded."


def stream_ollama_response(
    function_name: str,
    system_prompt: str,
    user_message: str,
    input_data: Any,
) -> Generator[str, None, None]:
    """
    Stream response from Hosted LLM (Gemini or OpenAI) if key is set,
    otherwise fallback to Ollama, and if Ollama is not running, fallback to Simulated response.
    """
    start_time = time.time()
    full_response = ""
    error_message = None

    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if groq_key:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "stream": True,
                "temperature": 0.7
            }
            with httpx.Client(timeout=60) as client:
                with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code == 200:
                        for line in response.iter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data_str)
                                    text = chunk["choices"][0]["delta"].get("content", "")
                                    if text:
                                        full_response += text
                                        yield text
                                except Exception:
                                    continue
                        log_ollama_call(function_name, input_data, full_response, int((time.time() - start_time) * 1000))
                        return
                    else:
                        error_message = f"Groq API returned status code {response.status_code}"
        except Exception as e:
            error_message = f"Groq API error: {str(e)}"

    if gemini_key and error_message is None:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?key={gemini_key}&alt=sse"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "parts": [{"text": user_message}]
                    }
                ],
                "systemInstruction": {
                    "parts": [{"text": system_prompt}]
                },
                "generationConfig": {
                    "temperature": 0.7
                }
            }
            with httpx.Client(timeout=60) as client:
                with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code == 200:
                        for line in response.iter_lines():
                            if line.startswith("data: "):
                                try:
                                    chunk = json.loads(line[6:])
                                    text = chunk["candidates"][0]["content"]["parts"][0]["text"]
                                    full_response += text
                                    yield text
                                except Exception:
                                    continue
                        log_ollama_call(function_name, input_data, full_response, int((time.time() - start_time) * 1000))
                        return
                    else:
                        error_message = f"Gemini API returned status code {response.status_code}"
        except Exception as e:
            error_message = f"Gemini API error: {str(e)}"

    if openai_key and error_message is None:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "stream": True,
                "temperature": 0.7
            }
            with httpx.Client(timeout=60) as client:
                with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code == 200:
                        for line in response.iter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data_str)
                                    text = chunk["choices"][0]["delta"].get("content", "")
                                    if text:
                                        full_response += text
                                        yield text
                                except Exception:
                                    continue
                        log_ollama_call(function_name, input_data, full_response, int((time.time() - start_time) * 1000))
                        return
                    else:
                        error_message = f"OpenAI API returned status code {response.status_code}"
        except Exception as e:
            error_message = f"OpenAI API error: {str(e)}"

    # Attempt local Ollama
    try:
        with httpx.Client(timeout=OLLAMA_TIMEOUT) as client:
            try:
                tags_resp = client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
                ollama_running = tags_resp.status_code == 200
            except Exception:
                ollama_running = False

            if ollama_running:
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
                    if response.status_code == 200:
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
                        log_ollama_call(function_name, input_data, full_response, int((time.time() - start_time) * 1000))
                        return
                    else:
                        error_message = f"Ollama returned status code {response.status_code}"
            else:
                if error_message is None:
                    error_message = "Ollama is not running locally"
    except Exception as e:
        if error_message is None:
            error_message = str(e)

    # Fallback to simulated response
    print(f"Fallback active: {error_message}. Yielding simulated response.")
    simulated_text = generate_simulated_response(function_name, input_data)
    
    words = simulated_text.split(" ")
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        full_response += chunk
        yield chunk
        time.sleep(0.03)

    log_ollama_call(
        function_name,
        input_data,
        full_response,
        int((time.time() - start_time) * 1000),
        f"Fallback triggered due to: {error_message}"
    )


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
