"""
Analytics router for KSP Analytics Platform MongoDB
Handles all analytics and insights endpoints
"""
from fastapi import APIRouter, Depends, Query
from pymongo.database import Database
from database import get_db
from services.analytics_service import (
    get_temporal_heatmap,
    get_anomalies,
    get_repeat_offenders,
    get_risk_scores_by_district,
    get_crime_hotspots_geojson,
    get_demographic_correlation,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/temporal-heatmap")
def temporal_heatmap(db: Database = Depends(get_db)):
    """
    Get temporal heatmap data (Hour vs Day of Week)
    Returns grid of crime counts for visualization
    """
    return {
        "data": get_temporal_heatmap(),
        "title": "Crime Temporal Distribution (Hour vs Day)",
        "xAxis": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "yAxis": list(range(24)),
    }


@router.get("/anomalies")
def anomalies(sensitivity: float = Query(2.0, ge=0.5, le=5.0), db: Database = Depends(get_db)):
    """
    Get anomalies in crime time series
    Anomalies are days with unusual crime spikes
    """
    return {
        "data": get_anomalies(sensitivity),
        "sensitivity": sensitivity,
        "description": "Days with crime counts significantly above normal",
    }


@router.get("/repeat-offenders")
def repeat_offenders(
    min_crimes: int = Query(3, ge=1, le=50),
    db: Database = Depends(get_db),
):
    """Get criminals with multiple offenses"""
    return {
        "data": get_repeat_offenders(min_crimes),
        "min_crimes_threshold": min_crimes,
    }


@router.get("/risk-scores")
def risk_scores(db: Database = Depends(get_db)):
    """Get district-level risk scores"""
    return {
        "data": get_risk_scores_by_district(),
        "scale": {
            "0-20": "Low Risk",
            "20-40": "Medium Risk",
            "40-60": "High Risk",
            "60-100": "Critical Risk",
        },
    }


@router.get("/hotspots-map")
def hotspots_map(db: Database = Depends(get_db)):
    """Get crime hotspots in GeoJSON format for map visualization"""
    return get_crime_hotspots_geojson()


@router.get("/demographics")
def demographics(db: Database = Depends(get_db)):
    """Get demographic correlations with crime"""
    return {
        "data": get_demographic_correlation(),
        "description": "Victim demographics and their correlation with crime types",
    }


@router.post("/report-snapshot")
def report_snapshot(
    date_from: str = Query(None),
    date_to: str = Query(None),
    districts: str = Query(None),
    crime_types: str = Query(None),
    db: Database = Depends(get_db),
):
    """
    Get analytics snapshot for report generation
    Includes all key metrics for the specified period and filters
    """
    from datetime import datetime
    from services.analytics_service import (
        get_crime_summary,
        get_district_stats,
        get_high_risk_zones,
        get_risk_scores_by_district,
    )
    
    # Parse filters
    districts_list = districts.split(",") if districts else None
    crime_types_list = crime_types.split(",") if crime_types else None
    
    # Calculate days between dates
    days = 30  # default
    if date_from and date_to:
        try:
            from_date = datetime.fromisoformat(date_from)
            to_date = datetime.fromisoformat(date_to)
            days = (to_date - from_date).days
        except ValueError:
            pass
    
    return {
        "summary": get_crime_summary(days),
        "district_stats": get_district_stats(days),
        "hotspots": get_high_risk_zones(),
        "risk_scores": get_risk_scores_by_district(),
        "period": {
            "from": date_from,
            "to": date_to,
            "days": days,
        },
        "filters": {
            "districts": districts_list,
            "crime_types": crime_types_list,
        },
    }
