from database import SessionLocal
from models import Report, User
from datetime import datetime, timedelta
import random

def seed_reports():
    db = SessionLocal()
    
    # Get a user
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_user = db.query(User).first()
        
    user_id = admin_user.id if admin_user else 1

    report_types = ["weekly", "monthly", "hotspot", "annual"]
    districts = ["Bengaluru Urban", "Mysuru", "Hubli", "Belagavi", "Mangaluru"]
    crime_types = ["theft", "assault", "fraud", "kidnapping", "murder", "cybercrime", "drugs"]

    reports = []
    now = datetime.utcnow()

    for i in range(15):
        report_type = random.choice(report_types)
        days_ago = random.randint(1, 30)
        created_at = now - timedelta(days=days_ago)
        
        if report_type == "weekly":
            date_from = created_at - timedelta(days=7)
        elif report_type == "monthly":
            date_from = created_at - timedelta(days=30)
        else:
            date_from = created_at - timedelta(days=365)
            
        r = Report(
            title=f"{report_type.capitalize()} Crime Report - {created_at.strftime('%Y-%b')}",
            description=f"Automated {report_type} summary of crime activities.",
            report_type=report_type,
            date_from=date_from,
            date_to=created_at,
            districts=random.sample(districts, random.randint(1, 3)),
            crime_types=random.sample(crime_types, random.randint(1, 4)),
            metrics={"total_crimes": random.randint(50, 500), "resolved": random.randint(10, 300)},
            narrative_summary="This report contains a summary of incidents based on selected parameters. Key trends indicate stable overall crime rates.",
            created_by=user_id,
            created_at=created_at
        )
        reports.append(r)

    db.add_all(reports)
    db.commit()
    print("Added dummy reports successfully!")
    db.close()

if __name__ == "__main__":
    seed_reports()
