from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Facility, Inspection, Finding, FindingStatus, InspectionStatus, AuditEvent, User, UserRole
from app.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics & BI"])

@router.get("/summary")
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Provides high-level KPI metrics, compliance ratios, and risk breakdowns for the dashboard."""
    # 1. Facility Metrics
    total_facilities = db.query(Facility).count()
    risk_breakdown = dict(
        db.query(Facility.risk_level, func.count(Facility.id))
        .group_by(Facility.risk_level)
        .all()
    )
    # Ensure all risk levels are present
    for r in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        risk_breakdown.setdefault(r, 0)

    category_breakdown = dict(
        db.query(Facility.category, func.count(Facility.id))
        .group_by(Facility.category)
        .all()
    )

    # 2. Inspection Metrics
    total_inspections = db.query(Inspection).count()
    status_breakdown = dict(
        db.query(Inspection.status, func.count(Inspection.id))
        .group_by(Inspection.status)
        .all()
    )
    for s in ["ASSIGNED", "IN_PROGRESS", "SUBMITTED", "COMPLETED", "REJECTED"]:
        status_breakdown.setdefault(s, 0)

    priority_breakdown = dict(
        db.query(Inspection.priority, func.count(Inspection.id))
        .group_by(Inspection.priority)
        .all()
    )

    # 3. Findings & Compliance Metrics
    total_findings = db.query(Finding).count()
    pass_findings = db.query(Finding).filter(Finding.status == FindingStatus.PASS).count()
    fail_findings = db.query(Finding).filter(Finding.status == FindingStatus.FAIL).count()
    na_findings = db.query(Finding).filter(Finding.status == FindingStatus.NA).count()

    compliance_rate = round((pass_findings / total_findings * 100), 1) if total_findings > 0 else 100.0

    # 4. Top Recurring Violations
    top_violations = (
        db.query(
            Finding.notes,
            func.count(Finding.id).label("count")
        )
        .filter(Finding.status == FindingStatus.FAIL, Finding.notes != None, Finding.notes != "")
        .group_by(Finding.notes)
        .order_by(func.count(Finding.id).desc())
        .limit(5)
        .all()
    )

    # 5. Inspector Activity Counts
    active_inspectors = db.query(User).filter(User.role == UserRole.INSPECTOR, User.is_active == True).count()

    # 6. Audit Health
    total_audits = db.query(AuditEvent).count()
    last_audit = db.query(AuditEvent).order_by(AuditEvent.id.desc()).first()

    return {
        "facilities": {
            "total": total_facilities,
            "by_risk": risk_breakdown,
            "by_category": category_breakdown
        },
        "inspections": {
            "total": total_inspections,
            "by_status": status_breakdown,
            "by_priority": priority_breakdown
        },
        "compliance": {
            "total_findings": total_findings,
            "passed": pass_findings,
            "failed": fail_findings,
            "na": na_findings,
            "compliance_rate_percent": compliance_rate,
            "top_violations": [{"issue": v[0], "occurrences": v[1]} for v in top_violations]
        },
        "inspectors_count": active_inspectors,
        "audit": {
            "total_records": total_audits,
            "last_event_type": last_audit.event_type if last_audit else "NONE",
            "last_event_time": last_audit.timestamp if last_audit else None
        },
        "generated_at": datetime.utcnow()
    }
