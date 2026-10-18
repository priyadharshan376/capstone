import os
import sys
from datetime import datetime, timedelta

# Disable C-extensions for Application Control / AppLocker environments
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models import (
    User, UserRole, Facility, RiskLevel, ChecklistTemplate, ChecklistItem,
    Inspection, InspectionStatus, Finding, FindingStatus, AuditEvent
)
from app.auth import get_password_hash, log_audit_event

def seed_database():
    print("🌱 Initializing Database Schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if users already exist
        if db.query(User).count() > 0:
            print("⚠️ Database already seeded! Skipping.")
            return

        print("👤 Creating Default System Users...")
        admin = User(
            email="admin@inspect.gov.in",
            hashed_password=get_password_hash("Admin@123"),
            full_name="Dr. Vikram Sen",
            role=UserRole.ADMIN,
            badge_number="ADMIN-HQ-01",
            is_active=True
        )
        supervisor = User(
            email="supervisor@inspect.gov.in",
            hashed_password=get_password_hash("Super@123"),
            full_name="Ananya Roy",
            role=UserRole.SUPERVISOR,
            badge_number="SUPV-SOUTH-04",
            is_active=True
        )
        inspector1 = User(
            email="rajesh@inspect.gov.in",
            hashed_password=get_password_hash("Insp@123"),
            full_name="Rajesh Sharma",
            role=UserRole.INSPECTOR,
            badge_number="INSP-2026-001",
            is_active=True
        )
        inspector2 = User(
            email="priya@inspect.gov.in",
            hashed_password=get_password_hash("Insp@123"),
            full_name="Priya Patel",
            role=UserRole.INSPECTOR,
            badge_number="INSP-2026-002",
            is_active=True
        )
        db.add_all([admin, supervisor, inspector1, inspector2])
        db.flush()

        print("🏭 Registering Sample Regulated Facilities...")
        facilities = [
            Facility(
                name="Apex Chemical & Fertilizer Plant",
                license_no="FAC-CHEM-2024-8891",
                category="Chemical & Hazardous",
                address="Plot 42, Industrial Growth Center, Peenya Phase 1, Bengaluru",
                latitude=13.0312,
                longitude=77.5186,
                risk_level=RiskLevel.HIGH,
                contact_person="Ramesh Kulkarni",
                contact_phone="+91 98450 11223"
            ),
            Facility(
                name="Golden Harvest Food Processing Hub",
                license_no="FAC-FOOD-2023-4120",
                category="Food Safety",
                address="Sector 9, KIADB Agro Food Park, Bidadi",
                latitude=12.8021,
                longitude=77.4014,
                risk_level=RiskLevel.MEDIUM,
                contact_person="Meera Nair",
                contact_phone="+91 98451 99887"
            ),
            Facility(
                name="Metro Care Super-Speciality Hospital",
                license_no="FAC-MED-2022-7711",
                category="Healthcare & Bio-Waste",
                address="15th Cross, Ring Road, Jayanagar, Bengaluru",
                latitude=12.9279,
                longitude=77.5815,
                risk_level=RiskLevel.CRITICAL,
                contact_person="Dr. Farhan Qureshi",
                contact_phone="+91 98452 44332"
            ),
            Facility(
                name="Skylight Infrastructure Towers Site",
                license_no="FAC-CONST-2025-0043",
                category="Construction & Civil Safety",
                address="Survey 108/2, Whitefield Main Road, Bengaluru",
                latitude=12.9698,
                longitude=77.7500,
                risk_level=RiskLevel.HIGH,
                contact_person="Sunil Verma",
                contact_phone="+91 98453 66778"
            ),
            Facility(
                name="GreenField Agro Cold Storage Unit 4",
                license_no="FAC-LOG-2021-9921",
                category="Cold Chain Logistics",
                address="National Highway 48, Nelamangala Tollgate",
                latitude=13.0978,
                longitude=77.3892,
                risk_level=RiskLevel.LOW,
                contact_person="K. Balakrishnan",
                contact_phone="+91 98454 88990"
            )
        ]
        db.add_all(facilities)
        db.flush()

        print("📋 Creating Standardized Inspection Checklist Templates...")
        # 1. Chemical Plant Checklist
        chk_chem = ChecklistTemplate(
            title="Hazardous Chemical & Environmental Compliance",
            category="Chemical & Hazardous",
            description="Statutory environmental and hazardous storage safety audit"
        )
        db.add(chk_chem)
        db.flush()

        chem_items = [
            ChecklistItem(template_id=chk_chem.id, question_text="Are Material Safety Data Sheets (MSDS) visibly posted at all storage tanks?", order_index=1),
            ChecklistItem(template_id=chk_chem.id, question_text="Is the automatic toxic gas leak detection and alarm system operational?", order_index=2),
            ChecklistItem(template_id=chk_chem.id, question_text="Are emergency eye wash and chemical drench showers functioning properly?", order_index=3),
            ChecklistItem(template_id=chk_chem.id, question_text="Is primary and secondary spill containment bunding free of cracks?", order_index=4),
            ChecklistItem(template_id=chk_chem.id, question_text="Are fire extinguishers inspected, tagged, and fully pressurized?", order_index=5),
        ]
        db.add_all(chem_items)

        # 2. Food Safety Checklist
        chk_food = ChecklistTemplate(
            title="Food Hygiene & Safe Manufacturing Standard",
            category="Food Safety",
            description="Sanitation, cold storage temperature, and hygiene compliance"
        )
        db.add(chk_food)
        db.flush()

        food_items = [
            ChecklistItem(template_id=chk_food.id, question_text="Are walk-in cold rooms maintained below 4°C with digital logs?", order_index=1),
            ChecklistItem(template_id=chk_food.id, question_text="Do food handlers wear mandatory hair nets, gloves, and clean aprons?", order_index=2),
            ChecklistItem(template_id=chk_food.id, question_text="Is potable water test certificate valid within the last 6 months?", order_index=3),
            ChecklistItem(template_id=chk_food.id, question_text="Are raw and cooked preparation areas strictly segregated?", order_index=4),
            ChecklistItem(template_id=chk_food.id, question_text="Is the electronic pest management program active and documented?", order_index=5),
        ]
        db.add_all(food_items)
        db.flush()

        print("📅 Scheduling Demonstrable Inspections...")
        now = datetime.utcnow()
        
        # Inspection 1: ASSIGNED (Ready for live demonstration on mobile app!)
        insp_live = Inspection(
            facility_id=facilities[0].id,
            inspector_id=inspector1.id,
            template_id=chk_chem.id,
            scheduled_date=now + timedelta(hours=2),
            status=InspectionStatus.ASSIGNED,
            priority="HIGH"
        )
        
        # Inspection 2: SUBMITTED (Ready for supervisor review on web dashboard!)
        insp_submitted = Inspection(
            facility_id=facilities[1].id,
            inspector_id=inspector2.id,
            template_id=chk_food.id,
            scheduled_date=now - timedelta(days=1),
            status=InspectionStatus.SUBMITTED,
            priority="NORMAL",
            submission_notes="Overall sanitation satisfactory. Minor temperature logging calibration needed in Cold Room 2.",
            submission_lat=12.8023,
            submission_lng=77.4016,
            submitted_at=now - timedelta(hours=3)
        )
        db.add_all([insp_live, insp_submitted])
        db.flush()

        # Findings for the submitted inspection
        findings = [
            Finding(
                inspection_id=insp_submitted.id,
                checklist_item_id=food_items[0].id,
                status=FindingStatus.PASS,
                notes="Cold room reading steady at 3.2°C.",
                gps_lat=12.8023,
                gps_lng=77.4016,
                captured_at=now - timedelta(hours=3)
            ),
            Finding(
                inspection_id=insp_submitted.id,
                checklist_item_id=food_items[1].id,
                status=FindingStatus.PASS,
                notes="All 14 staff members present comply with safety gear regulations.",
                gps_lat=12.8023,
                gps_lng=77.4016,
                captured_at=now - timedelta(hours=3)
            ),
            Finding(
                inspection_id=insp_submitted.id,
                checklist_item_id=food_items[2].id,
                status=FindingStatus.FAIL,
                notes="Last water test report expired 15 days ago. Renewal pending.",
                gps_lat=12.8023,
                gps_lng=77.4016,
                captured_at=now - timedelta(hours=3)
            ),
            Finding(
                inspection_id=insp_submitted.id,
                checklist_item_id=food_items[3].id,
                status=FindingStatus.PASS,
                notes="Physical separation walls installed between raw handling and baking.",
                gps_lat=12.8023,
                gps_lng=77.4016,
                captured_at=now - timedelta(hours=3)
            ),
            Finding(
                inspection_id=insp_submitted.id,
                checklist_item_id=food_items[4].id,
                status=FindingStatus.PASS,
                notes="UV insect light traps inspected and clean.",
                gps_lat=12.8023,
                gps_lng=77.4016,
                captured_at=now - timedelta(hours=3)
            ),
        ]
        db.add_all(findings)

        print("🔒 Generating Initial Cryptographic Audit Log Entries...")
        log_audit_event(
            db=db,
            event_type="SYSTEM_INITIALIZED",
            actor_id=admin.id,
            actor_name=admin.full_name,
            entity_type="System",
            entity_id=1,
            details="System database schema and default policies initialized"
        )
        log_audit_event(
            db=db,
            event_type="INSPECTION_ASSIGNED",
            actor_id=supervisor.id,
            actor_name=supervisor.full_name,
            entity_type="Inspection",
            entity_id=insp_live.id,
            details=f"Assigned live inspection for {facilities[0].name} to {inspector1.full_name}"
        )
        log_audit_event(
            db=db,
            event_type="INSPECTION_SUBMITTED",
            actor_id=inspector2.id,
            actor_name=inspector2.full_name,
            entity_type="Inspection",
            entity_id=insp_submitted.id,
            details=f"Submitted field findings for {facilities[1].name} with GPS coordinates"
        )

        db.commit()
        print("✅ Database seeding complete! Ready for demo.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
