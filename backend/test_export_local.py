import os
import sys
from database import SessionLocal
from models import Report, Crime
from services.export_service import export_report_to_pdf
from datetime import datetime, UTC

def test():
    db = SessionLocal()
    report_id = 4
    report = db.query(Report).filter(Report.id == report_id).first()
    print("Report:", report)
    
    crimes = db.query(Crime).filter(
        Crime.date >= report.date_from,
        Crime.date <= report.date_to
    ).all()
    
    crime_data = [
        {
            "crime_id": c.crime_id,
            "type": c.type,
            "district": c.district,
            "date": c.date.strftime("%Y-%m-%d"),
            "status": c.status,
            "severity": c.severity,
        }
        for c in crimes
    ]
    
    date_range = f"{report.date_from.strftime('%Y-%m-%d')} to {report.date_to.strftime('%Y-%m-%d')}"
    
    try:
        pdf_bytes = export_report_to_pdf(
            title=report.title,
            date_range=date_range,
            summary=report.metrics,
            narrative=report.narrative_summary or "",
            crime_data=crime_data,
        )
        print("Success, length:", len(pdf_bytes))
        
        filename = f"{report.title.replace(' ', '_')}_{datetime.now(UTC).strftime('%Y%m%d')}.pdf"
        print("Filename:", filename)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
