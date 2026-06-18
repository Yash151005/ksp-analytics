"""
Reports router for KSP Analytics Platform MongoDB
Handles report generation and export
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from pymongo.database import Database
from bson.objectid import ObjectId
from typing import List, Optional
from datetime import datetime, timedelta, UTC
from database import get_db
from models import serialize_docs, serialize_doc
from services.export_service import (
    export_report_to_pdf,
    create_excel_report,
    export_analytics_to_json,
    export_crimes_to_csv,
)
from services.analytics_service import (
    get_crime_summary,
    get_district_stats,
    get_high_risk_zones,
    get_risk_scores_by_district,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])

# Pre-defined report templates
REPORT_TEMPLATES = {
    "Weekly District Report": {
        "title": "Weekly District Crime Report",
        "days": 7,
        "metrics": ["total_crimes", "clearance_rate", "crime_by_type"],
    },
    "Monthly Executive Briefing": {
        "title": "Monthly Executive Crime Briefing",
        "days": 30,
        "metrics": ["summary", "district_stats", "hotspots", "risk_scores"],
    },
    "Hotspot Analysis": {
        "title": "Crime Hotspot Analysis Report",
        "days": 90,
        "metrics": ["hotspots", "temporal_patterns", "demographic_data"],
    },
}

class ExportRequest(BaseModel):
    format: str = "pdf"

class GenerateReportRequest(BaseModel):
    title: str
    report_type: str = "custom"
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    districts: Optional[str] = None
    crime_types: Optional[str] = None

class UpdateReportRequest(BaseModel):
    title: str
    report_type: str
    districts: Optional[str] = None
    crime_types: Optional[str] = None


@router.get("/")
def list_reports(
    report_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Database = Depends(get_db),
):
    """List generated reports"""
    filter_query = {}
    
    if report_type:
        filter_query["report_type"] = report_type
    
    total = db.reports.count_documents(filter_query)
    reports = list(db.reports.find(filter_query).sort("created_at", -1).skip(offset).limit(limit))
    
    data = []
    for r in reports:
        data.append({
            "id": str(r["_id"]),
            "title": r.get("title"),
            "report_type": r.get("report_type"),
            "date_from": r.get("date_from").isoformat() if isinstance(r.get("date_from"), datetime) else r.get("date_from"),
            "date_to": r.get("date_to").isoformat() if isinstance(r.get("date_to"), datetime) else r.get("date_to"),
            "created_at": r.get("created_at").isoformat() if isinstance(r.get("created_at"), datetime) else r.get("created_at"),
        })
    
    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/templates")
def get_templates():
    """Get available report templates"""
    return {
        "templates": list(REPORT_TEMPLATES.keys()),
        "details": REPORT_TEMPLATES,
    }


@router.post("/generate")
def generate_report(
    req: GenerateReportRequest,
    db: Database = Depends(get_db),
):
    """Generate a new report"""
    # Parse dates
    try:
        if req.date_from:
            from_date = datetime.fromisoformat(req.date_from)
        else:
            from_date = datetime.now(UTC) - timedelta(days=30)
        
        if req.date_to:
            to_date = datetime.fromisoformat(req.date_to)
        else:
            to_date = datetime.now(UTC)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    
    # Parse filters
    districts_list = [d.strip() for d in req.districts.split(",") if d.strip()] if req.districts else []
    crime_types_list = [c.strip() for c in req.crime_types.split(",") if c.strip()] if req.crime_types else []
    
    # Build query
    filter_query = {"date": {"$gte": from_date, "$lte": to_date}}
    
    if districts_list:
        filter_query["district"] = {"$in": districts_list}
    
    if crime_types_list:
        filter_query["type"] = {"$in": crime_types_list}
    
    crimes = list(db.crimes.find(filter_query))
    
    # Calculate metrics
    metrics = {
        "total_crimes": len(crimes),
        "crime_by_type": {},
        "crime_by_district": {},
        "avg_severity": 0,
        "avg_clearance_rate": 0,
    }
    
    if crimes:
        for crime in crimes:
            c_type = crime.get("type", "Unknown")
            c_dist = crime.get("district", "Unknown")
            metrics["crime_by_type"][c_type] = metrics["crime_by_type"].get(c_type, 0) + 1
            metrics["crime_by_district"][c_dist] = metrics["crime_by_district"].get(c_dist, 0) + 1
        
        total_severity = sum(c.get("severity", 0) for c in crimes)
        metrics["avg_severity"] = round(total_severity / len(crimes), 2)
        
        closed = sum(1 for c in crimes if c.get("status") == "closed")
        metrics["avg_clearance_rate"] = round((closed / len(crimes) * 100), 2)
    
    # Create report
    now = datetime.now(UTC)
    report_doc = {
        "title": req.title,
        "report_type": req.report_type,
        "date_from": from_date,
        "date_to": to_date,
        "districts": districts_list,
        "crime_types": crime_types_list,
        "metrics": metrics,
        "created_at": now,
        "narrative_summary": None,
    }
    
    result = db.reports.insert_one(report_doc)
    
    return {
        "id": str(result.inserted_id),
        "title": req.title,
        "report_type": req.report_type,
        "date_from": from_date.isoformat(),
        "date_to": to_date.isoformat(),
        "metrics": metrics,
        "created_at": now.isoformat(),
    }


@router.get("/{report_id}")
def get_report(report_id: str, db: Database = Depends(get_db)):
    """Get report details"""
    try:
        obj_id = ObjectId(report_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid report ID format")
        
    report = db.reports.find_one({"_id": obj_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    result = serialize_doc(report)
    
    if "date_from" in result and isinstance(result["date_from"], datetime):
        result["date_from"] = result["date_from"].isoformat()
    if "date_to" in result and isinstance(result["date_to"], datetime):
        result["date_to"] = result["date_to"].isoformat()
    if "created_at" in result and isinstance(result["created_at"], datetime):
        result["created_at"] = result["created_at"].isoformat()
        
    return result


@router.put("/{report_id}")
def update_report(
    report_id: str,
    req: UpdateReportRequest,
    db: Database = Depends(get_db)
):
    """Update report metadata and recalculate metrics"""
    try:
        obj_id = ObjectId(report_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid report ID format")
        
    existing_report = db.reports.find_one({"_id": obj_id})
    if not existing_report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    districts_list = [d.strip() for d in req.districts.split(",") if d.strip()] if req.districts else []
    crime_types_list = [c.strip() for c in req.crime_types.split(",") if c.strip()] if req.crime_types else []
    
    # Build query
    filter_query = {"date": {"$gte": existing_report["date_from"], "$lte": existing_report["date_to"]}}
    
    if districts_list:
        filter_query["district"] = {"$in": districts_list}
    
    if crime_types_list:
        filter_query["type"] = {"$in": crime_types_list}
    
    crimes = list(db.crimes.find(filter_query))
    
    # Calculate metrics
    metrics = {
        "total_crimes": len(crimes),
        "crime_by_type": {},
        "crime_by_district": {},
        "avg_severity": 0,
        "avg_clearance_rate": 0,
    }
    
    if crimes:
        for crime in crimes:
            c_type = crime.get("type", "Unknown")
            c_dist = crime.get("district", "Unknown")
            metrics["crime_by_type"][c_type] = metrics["crime_by_type"].get(c_type, 0) + 1
            metrics["crime_by_district"][c_dist] = metrics["crime_by_district"].get(c_dist, 0) + 1
        
        total_severity = sum(c.get("severity", 0) for c in crimes)
        metrics["avg_severity"] = round(total_severity / len(crimes), 2)
        
        closed = sum(1 for c in crimes if c.get("status") == "closed")
        metrics["avg_clearance_rate"] = round((closed / len(crimes) * 100), 2)
    
    update_data = {
        "title": req.title,
        "report_type": req.report_type,
        "districts": districts_list,
        "crime_types": crime_types_list,
        "metrics": metrics
    }
    
    db.reports.update_one({"_id": obj_id}, {"$set": update_data})
        
    return {"message": "Report updated successfully", "metrics": metrics}


@router.delete("/{report_id}")
def delete_report(report_id: str, db: Database = Depends(get_db)):
    """Delete a report"""
    try:
        obj_id = ObjectId(report_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid report ID format")
        
    result = db.reports.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
        
    return {"message": "Report deleted successfully"}


@router.post("/{report_id}/export")
def export_report(
    report_id: str,
    req: ExportRequest,
    db: Database = Depends(get_db),
):
    """Export report in specified format"""
    format = req.format
    try:
        obj_id = ObjectId(report_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid report ID format")
        
    report = db.reports.find_one({"_id": obj_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Get crimes for report period
    filter_query = {
        "date": {
            "$gte": report["date_from"],
            "$lte": report["date_to"]
        }
    }
    
    if report.get("districts"):
        filter_query["district"] = {"$in": report["districts"]}
        
    if report.get("crime_types"):
        filter_query["type"] = {"$in": report["crime_types"]}
        
    crimes = list(db.crimes.find(filter_query))
    
    # Prepare crime data for export
    crime_data = []
    for c in crimes:
        c_date = c.get("date")
        date_str = c_date.strftime("%Y-%m-%d") if isinstance(c_date, datetime) else str(c_date)
        crime_data.append({
            "crime_id": c.get("crime_id"),
            "type": c.get("type"),
            "district": c.get("district"),
            "date": date_str,
            "status": c.get("status"),
            "severity": c.get("severity"),
        })
    
    d_from = report.get("date_from").strftime('%Y-%m-%d') if isinstance(report.get("date_from"), datetime) else report.get("date_from")
    d_to = report.get("date_to").strftime('%Y-%m-%d') if isinstance(report.get("date_to"), datetime) else report.get("date_to")
    date_range = f"{d_from} to {d_to}"
    
    title_safe = report.get("title", "Report").replace(" ", "_")
    timestamp = datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
    
    if format == "pdf":
        pdf_bytes = export_report_to_pdf(
            title=report.get("title", "Report"),
            date_range=date_range,
            summary=report.get("metrics", {}),
            narrative=report.get("narrative_summary") or "",
            crime_data=crime_data,
        )
        filename = f"{title_safe}_{timestamp}.pdf"
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    
    elif format == "csv":
        csv_data = export_crimes_to_csv(crimes)
        filename = f"{title_safe}_{timestamp}.csv"
        return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    
    elif format == "json":
        json_data = export_analytics_to_json({
            "title": report.get("title", "Report"),
            "date_range": date_range,
            "metrics": report.get("metrics", {}),
            "crimes": crime_data,
        })
        filename = f"{title_safe}_{timestamp}.json"
        return Response(content=json_data, media_type="application/json", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    
    elif format == "xlsx":
        excel_bytes = create_excel_report(
            title=report.get("title", "Report"),
            data_sheets={
                "Summary": [report.get("metrics", {})],
                "Crimes": crime_data,
            }
        )
        filename = f"{title_safe}_{timestamp}.xlsx"
        return Response(content=excel_bytes, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/snapshot/data")
def get_report_snapshot(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Database = Depends(get_db),
):
    """Get snapshot data for report preview"""
    # Parse dates
    if date_from:
        from_date = datetime.fromisoformat(date_from)
    else:
        from_date = datetime.now(UTC) - timedelta(days=30)
    
    if date_to:
        to_date = datetime.fromisoformat(date_to)
    else:
        to_date = datetime.now(UTC)
    
    days = (to_date - from_date).days
    if days < 1:
        days = 1
    
    return {
        "summary": get_crime_summary(days),
        "district_stats": get_district_stats(days),
        "hotspots": get_high_risk_zones(),
        "risk_scores": get_risk_scores_by_district(),
        "period": {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "days": days,
        },
    }
