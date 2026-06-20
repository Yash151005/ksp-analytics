"""
Analytics service for KSP Analytics Platform MongoDB
Handles data analysis, aggregations, and statistics
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Any
from database import get_db_instance

class DatabaseProxy:
    def __getattr__(self, name):
        return getattr(get_db_instance(), name)

db = DatabaseProxy()


def get_crime_summary(days: int = 30) -> Dict[str, Any]:
    """
    Get summary statistics for crimes in the last N days
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    total_crimes = db.crimes.count_documents({"date": {"$gte": cutoff_date}})
    
    # Crimes by status
    status_pipeline = [
        {"$match": {"date": {"$gte": cutoff_date}}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_stats = list(db.crimes.aggregate(status_pipeline))
    status_dict = {item["_id"]: item["count"] for item in status_stats if item["_id"]}
    
    # Crime by type
    type_pipeline = [
        {"$match": {"date": {"$gte": cutoff_date}}},
        {"$group": {"_id": "$type", "count": {"$sum": 1}}}
    ]
    type_stats = list(db.crimes.aggregate(type_pipeline))
    type_dict = {item["_id"]: item["count"] for item in type_stats if item["_id"]}
    
    # Calculate clearance rate (closed / total)
    closed_crimes = status_dict.get("closed", 0)
    clearance_rate = (closed_crimes / total_crimes * 100) if total_crimes > 0 else 0
    
    return {
        "total_crimes": total_crimes,
        "closed_crimes": closed_crimes,
        "open_crimes": status_dict.get("open", 0),
        "under_investigation": status_dict.get("under_investigation", 0),
        "clearance_rate": round(clearance_rate, 2),
        "crime_by_type": type_dict,
        "crime_by_status": status_dict,
    }


def get_district_stats(days: int = 30) -> Dict[str, int]:
    """Get crime counts by district"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    pipeline = [
        {"$match": {"date": {"$gte": cutoff_date}}},
        {"$group": {"_id": "$district", "count": {"$sum": 1}}}
    ]
    
    district_stats = list(db.crimes.aggregate(pipeline))
    return {item["_id"]: item["count"] for item in district_stats if item["_id"]}


def get_crime_trend(months: int = 12) -> List[Dict[str, Any]]:
    """Get crime trends by month"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30 * months)
    
    crimes = list(db.crimes.find({"date": {"$gte": cutoff_date}}))
    
    # Group by month
    monthly_data = {}
    for crime in crimes:
        c_date = crime.get("date")
        if isinstance(c_date, datetime):
            month_key = c_date.strftime("%Y-%m")
        else:
            try:
                month_key = datetime.fromisoformat(str(c_date)).strftime("%Y-%m")
            except:
                continue
                
        if month_key not in monthly_data:
            monthly_data[month_key] = {"date": month_key, "count": 0, "severity_avg": 0}
        monthly_data[month_key]["count"] += 1
        monthly_data[month_key]["severity_avg"] = (
            (monthly_data[month_key]["severity_avg"] + crime.get("severity", 0)) / 2
        )
    
    return sorted(monthly_data.values(), key=lambda x: x["date"])


def get_high_risk_zones(min_incidents: int = 10) -> List[Dict[str, Any]]:
    """Identify high-crime zones based on incident clusters"""
    pipeline = [
        {"$group": {
            "_id": {"district": "$district", "taluk": "$taluk"},
            "count": {"$sum": 1},
            "avg_severity": {"$avg": "$severity"},
            "avg_lat": {"$avg": "$latitude"},
            "avg_lng": {"$avg": "$longitude"}
        }},
        {"$match": {"count": {"$gte": min_incidents}}}
    ]
    
    district_stats = list(db.crimes.aggregate(pipeline))
    
    zones = []
    for stat in district_stats:
        district = stat["_id"].get("district")
        taluk = stat["_id"].get("taluk")
        count = stat["count"]
        severity = stat.get("avg_severity", 0)
        lat = stat.get("avg_lat")
        lng = stat.get("avg_lng")
        
        risk_score = min(100, count * 5 + (severity or 0) * 10)
        zones.append({
            "district": district,
            "taluk": taluk,
            "incidents": count,
            "avg_severity": round(severity, 2) if severity else 0,
            "risk_score": round(risk_score, 2),
            "latitude": lat,
            "longitude": lng,
        })
    
    return sorted(zones, key=lambda x: x["risk_score"], reverse=True)


def get_temporal_heatmap() -> List[Dict[str, Any]]:
    """
    Generate heatmap data: Hour of day (Y) vs Day of week (X)
    Returns grid of crime counts
    """
    pipeline = [
        {"$project": {
            "day_of_week": 1,
            "hour": {"$toInt": {"$arrayElemAt": [{"$split": ["$time", ":"]}, 0]}}
        }},
        {"$group": {
            "_id": {"day": "$day_of_week", "hour": "$hour"},
            "count": {"$sum": 1}
        }}
    ]
    
    results = list(db.crimes.aggregate(pipeline))
    
    # Initialize grid
    hours = range(24)
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    
    # create lookup dict
    lookup = { (r["_id"]["day"].lower() if r["_id"]["day"] else "", r["_id"]["hour"]): r["count"] for r in results }
    
    heatmap_data = []
    
    for day_idx, day in enumerate(days):
        for hour in hours:
            count = lookup.get((day, hour), 0)
            heatmap_data.append({
                "day": day,
                "day_index": day_idx,
                "hour": hour,
                "count": count,
                "intensity": min(100, count * 10),  # 0-100 scale
            })
    
    return heatmap_data


def get_anomalies(sensitivity: float = 2.0) -> List[Dict[str, Any]]:
    """
    Detect anomalies in crime time series
    Uses simple standard deviation approach
    """
    # Get daily crime counts for last 90 days
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
    
    crimes = list(db.crimes.find({"date": {"$gte": cutoff_date}}))
    
    daily_crimes = {}
    for crime in crimes:
        c_date = crime.get("date")
        if isinstance(c_date, datetime):
            day_key = c_date.strftime("%Y-%m-%d")
        else:
            try:
                day_key = datetime.fromisoformat(str(c_date)).strftime("%Y-%m-%d")
            except:
                continue
        daily_crimes[day_key] = daily_crimes.get(day_key, 0) + 1
    
    if not daily_crimes:
        return []
    
    # Calculate mean and std dev
    values = list(daily_crimes.values())
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std_dev = variance ** 0.5
    
    # Find anomalies (values > mean + sensitivity * std_dev)
    threshold = mean + (sensitivity * std_dev)
    
    anomalies = []
    for date_str, count in daily_crimes.items():
        if count > threshold:
            anomalies.append({
                "date": date_str,
                "crime_count": count,
                "expected_count": round(mean, 2),
                "deviation": round(count - mean, 2),
                "severity": min(100, int((count - mean) / std_dev * 25)) if std_dev > 0 else 0,
            })
    
    return sorted(anomalies, key=lambda x: x["crime_count"], reverse=True)


def get_repeat_offenders(min_crimes: int = 3) -> List[Dict[str, Any]]:
    """Get criminals with multiple offenses"""
    criminals = list(db.criminals.find({}))
    
    repeat_offenders = []
    for criminal in criminals:
        crime_count = len(criminal.get("crime_history", []))
        if crime_count >= min_crimes:
            repeat_offenders.append({
                "id": str(criminal["_id"]),
                "name": criminal.get("name"),
                "alias": criminal.get("alias"),
                "crime_count": crime_count,
                "risk_score": criminal.get("risk_score"),
                "status": criminal.get("status"),
                "last_known_location": criminal.get("last_known_location"),
            })
    
    return sorted(repeat_offenders, key=lambda x: x["crime_count"], reverse=True)


def get_risk_scores_by_district() -> List[Dict[str, Any]]:
    """Calculate risk scores for each district"""
    # Get crime data by district for last 30 days
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    pipeline = [
        {"$match": {"date": {"$gte": cutoff_date}}},
        {"$group": {
            "_id": "$district",
            "crime_count": {"$sum": 1},
            "avg_severity": {"$avg": "$severity"}
        }}
    ]
    
    district_crimes = list(db.crimes.aggregate(pipeline))
    
    risk_scores = []
    for item in district_crimes:
        district = item.get("_id")
        if not district:
            continue
            
        crime_count = item.get("crime_count", 0)
        avg_severity = item.get("avg_severity", 0)
        
        # Risk score calculation: 40% crime count, 60% severity
        count_score = min(100, crime_count * 2)
        severity_score = (avg_severity / 5) * 100
        overall_risk = (count_score * 0.4) + (severity_score * 0.6)
        
        risk_scores.append({
            "district": district,
            "risk_score": round(overall_risk, 2),
            "crime_count_30d": crime_count,
            "avg_severity": round(avg_severity, 2),
            "trend": "up" if crime_count > 10 else "stable",
        })
    
    return sorted(risk_scores, key=lambda x: x["risk_score"], reverse=True)


def get_crime_hotspots_geojson() -> Dict[str, Any]:
    """
    Get crime hotspots in GeoJSON format for map visualization
    """
    crimes = list(db.crimes.find({"latitude": {"$ne": None}, "longitude": {"$ne": None}}))
    
    features = []
    for crime in crimes:
        c_date = crime.get("date")
        if isinstance(c_date, datetime):
            date_str = c_date.isoformat()
        else:
            date_str = str(c_date)
            
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [crime.get("longitude"), crime.get("latitude")],
            },
            "properties": {
                "id": str(crime["_id"]),
                "crime_id": crime.get("crime_id"),
                "type": crime.get("type"),
                "severity": crime.get("severity"),
                "date": date_str,
                "status": crime.get("status"),
                "district": crime.get("district"),
            },
        })
    
    return {
        "type": "FeatureCollection",
        "features": features,
    }


def get_demographic_correlation() -> Dict[str, Any]:
    """
    Get correlations between victim demographics and crime types
    """
    crimes = list(db.crimes.find({}))
    
    age_distribution = {}
    gender_distribution = {}
    occupation_distribution = {}
    total_victims = 0
    
    for crime in crimes:
        victims = crime.get("victims", [])
        total_victims += len(victims)
        for victim in victims:
            age = victim.get("age")
            if age is not None:
                age_bucket = f"{(age // 10) * 10}-{((age // 10) + 1) * 10}"
                age_distribution[age_bucket] = age_distribution.get(age_bucket, 0) + 1
            
            gender = victim.get("gender")
            if gender:
                gender_distribution[gender] = gender_distribution.get(gender, 0) + 1
            
            occupation = victim.get("occupation")
            if occupation:
                occupation_distribution[occupation] = occupation_distribution.get(occupation, 0) + 1
    
    return {
        "age_distribution": age_distribution,
        "gender_distribution": gender_distribution,
        "occupation_distribution": occupation_distribution,
        "total_victims": total_victims,
    }


def get_active_criminals_count() -> int:
    """Get count of active criminals"""
    return db.criminals.count_documents({"status": "active"})


def get_high_risk_criminals(min_risk_score: float = 70) -> List[Dict[str, Any]]:
    """Get high-risk criminals above threshold"""
    criminals = list(db.criminals.find({"risk_score": {"$gte": min_risk_score}}))
    
    result = []
    for criminal in criminals:
        result.append({
            "id": str(criminal["_id"]),
            "name": criminal.get("name"),
            "alias": criminal.get("alias"),
            "risk_score": criminal.get("risk_score"),
            "status": criminal.get("status"),
            "crime_count": len(criminal.get("crime_history", [])),
            "associates_count": len(criminal.get("associated_criminal_ids", [])),
        })
    
    return sorted(result, key=lambda x: x["risk_score"], reverse=True)
