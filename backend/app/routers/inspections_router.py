import os
import math
import random
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import (
    Inspection, Facility, User, UserRole, ChecklistTemplate, ChecklistItem,
    Finding, InspectionStatus, FindingStatus
)
from app.schemas import (
    InspectionAssignRequest, InspectionSubmissionRequest,
    SupervisorReviewRequest, InspectionResponse, InspectionDetailResponse
)
from app.auth import get_current_user, require_role, log_audit_event

router = APIRouter(prefix="/inspections", tags=["Inspections"])

def build_inspection_response(insp: Inspection) -> dict:
    findings_list = []
    photos = []
    if insp.findings:
        for f in insp.findings:
            if f.photo_url and f.photo_url.strip() and f.photo_url not in photos:
                photos.append(f.photo_url)
            findings_list.append({
                "id": f.id,
                "checklist_item_id": f.checklist_item_id,
                "question_text": f.checklist_item.question_text if f.checklist_item else f"Question #{f.checklist_item_id}",
                "status": f.status,
                "notes": f.notes,
                "photo_url": f.photo_url,
                "gps_lat": f.gps_lat,
                "gps_lng": f.gps_lng,
                "captured_at": f.captured_at
            })

    return {
        "id": insp.id,
        "facility_id": insp.facility_id,
        "facility_name": insp.facility.name if insp.facility else None,
        "facility_category": insp.facility.category if insp.facility else None,
        "inspector_id": insp.inspector_id,
        "inspector_name": insp.inspector.full_name if insp.inspector else "Unassigned",
        "template_id": insp.template_id,
        "scheduled_date": insp.scheduled_date,
        "status": insp.status,
        "priority": insp.priority,
        "submission_lat": insp.submission_lat,
        "submission_lng": insp.submission_lng,
        "submitted_at": insp.submitted_at,
        "supervisor_feedback": insp.supervisor_feedback,
        "reviewed_at": insp.reviewed_at,
        "reviewed_by": insp.reviewed_by,
        "created_at": insp.created_at,
        "photos": photos,
        "photo_count": len(photos),
        "findings": findings_list
    }

@router.get("", response_model=List[InspectionResponse])
def get_inspections(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    facility_id: Optional[int] = Query(None),
    inspector_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None, description="Search across facility name, inspector name, or notes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Inspection)

    # Role-based filtering: Inspector only sees their own assigned inspections
    if current_user.role == UserRole.INSPECTOR:
        query = query.filter(Inspection.inspector_id == current_user.id)
    elif inspector_id:
        query = query.filter(Inspection.inspector_id == inspector_id)

    if facility_id:
        query = query.filter(Inspection.facility_id == facility_id)

    if priority:
        query = query.filter(Inspection.priority == priority.upper())

    if status:
        query = query.filter(Inspection.status == status.upper())

    if q:
        search_filter = f"%{q}%"
        query = query.join(Facility, isouter=True).join(User, isouter=True).filter(
            or_(
                Facility.name.ilike(search_filter),
                Facility.category.ilike(search_filter),
                User.full_name.ilike(search_filter),
                Inspection.submission_notes.ilike(search_filter)
            )
        )

    inspections = query.order_by(Inspection.scheduled_date.desc()).all()
    return [build_inspection_response(insp) for insp in inspections]

@router.post("/assign", response_model=InspectionResponse)
def assign_inspection(
    assign_in: InspectionAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR]))
):
    facility = db.query(Facility).filter(Facility.id == assign_in.facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    template = db.query(ChecklistTemplate).filter(ChecklistTemplate.id == assign_in.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Checklist template not found")

    inspector_id = assign_in.inspector_id
    # If no inspector specified, perform Fair Random Assignment across active inspectors
    if not inspector_id:
        available_inspectors = db.query(User).filter(
            User.role == UserRole.INSPECTOR,
            User.is_active == True
        ).all()
        if not available_inspectors:
            raise HTTPException(status_code=400, detail="No active inspectors available for assignment")
        chosen_inspector = random.choice(available_inspectors)
        inspector_id = chosen_inspector.id

    new_inspection = Inspection(
        facility_id=facility.id,
        inspector_id=inspector_id,
        template_id=template.id,
        scheduled_date=assign_in.scheduled_date,
        status=InspectionStatus.ASSIGNED,
        priority=assign_in.priority
    )
    db.add(new_inspection)
    db.commit()
    db.refresh(new_inspection)

    inspector = db.query(User).filter(User.id == inspector_id).first()

    log_audit_event(
        db=db,
        event_type="INSPECTION_ASSIGNED",
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        entity_type="Inspection",
        entity_id=new_inspection.id,
        details=f"Assigned inspection for '{facility.name}' to {inspector.full_name if inspector else 'None'} (Scheduled: {new_inspection.scheduled_date})"
    )

    return build_inspection_response(new_inspection)

@router.get("/{inspection_id}", response_model=InspectionDetailResponse)
def get_inspection_detail(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    insp = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")

    # Inspector access control check
    if current_user.role == UserRole.INSPECTOR and insp.inspector_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to view this inspection")

    res = build_inspection_response(insp)
    res["facility"] = insp.facility
    res["findings"] = [
        {
            "id": f.id,
            "checklist_item_id": f.checklist_item_id,
            "question_text": f.checklist_item.question_text if f.checklist_item else "",
            "status": f.status,
            "notes": f.notes,
            "photo_url": f.photo_url,
            "gps_lat": f.gps_lat,
            "gps_lng": f.gps_lng,
            "captured_at": f.captured_at
        }
        for f in insp.findings
    ]
    return res

@router.patch("/{inspection_id}/start", response_model=InspectionResponse)
def start_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    insp = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")

    if current_user.role == UserRole.INSPECTOR and insp.inspector_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to start this inspection")

    insp.status = InspectionStatus.IN_PROGRESS
    db.commit()
    db.refresh(insp)

    log_audit_event(
        db=db,
        event_type="INSPECTION_STARTED",
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        entity_type="Inspection",
        entity_id=insp.id,
        details=f"Inspector began on-site evaluation for {insp.facility.name}"
    )

    return build_inspection_response(insp)

@router.post("/{inspection_id}/upload-photo")
async def upload_evidence_photo(
    inspection_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    insp = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")

    ext = os.path.splitext(file.filename)[1] or ".jpg"
    unique_filename = f"insp_{inspection_id}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    public_url = f"/uploads/{unique_filename}"
    return {"photo_url": public_url, "filename": unique_filename}

@router.post("/{inspection_id}/submit", response_model=InspectionResponse)
def submit_inspection(
    inspection_id: int,
    submission: InspectionSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    insp = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")

    if current_user.role == UserRole.INSPECTOR and insp.inspector_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to submit this inspection")

    now = datetime.utcnow()
    insp.status = InspectionStatus.SUBMITTED
    insp.submission_notes = submission.submission_notes
    insp.submission_lat = submission.submission_lat
    insp.submission_lng = submission.submission_lng
    insp.submitted_at = now

    # Remove existing findings if any (for idempotent submission)
    db.query(Finding).filter(Finding.inspection_id == insp.id).delete()

    for item in submission.findings:
        finding = Finding(
            inspection_id=insp.id,
            checklist_item_id=item.checklist_item_id,
            status=item.status,
            notes=item.notes,
            photo_url=item.photo_url,
            gps_lat=item.gps_lat or submission.submission_lat,
            gps_lng=item.gps_lng or submission.submission_lng,
            captured_at=now
        )
        db.add(finding)

    db.commit()
    db.refresh(insp)

    log_audit_event(
        db=db,
        event_type="INSPECTION_SUBMITTED",
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        entity_type="Inspection",
        entity_id=insp.id,
        details=f"Inspection submitted with GPS ({submission.submission_lat}, {submission.submission_lng}) and {len(submission.findings)} findings"
    )

    return build_inspection_response(insp)

@router.post("/{inspection_id}/review", response_model=InspectionResponse)
def review_inspection(
    inspection_id: int,
    review_in: SupervisorReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR]))
):
    insp = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")

    new_status = review_in.status.upper()
    if new_status not in [InspectionStatus.COMPLETED, InspectionStatus.REJECTED]:
        raise HTTPException(status_code=400, detail="Review status must be either 'COMPLETED' or 'REJECTED'")

    now = datetime.utcnow()
    insp.status = new_status
    insp.supervisor_feedback = review_in.supervisor_feedback
    insp.reviewed_at = now
    insp.reviewed_by = current_user.full_name

    db.commit()
    db.refresh(insp)

    log_audit_event(
        db=db,
        event_type="INSPECTION_REVIEWED",
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        entity_type="Inspection",
        entity_id=insp.id,
        details=f"Supervisor marked report as {new_status}. Feedback: {review_in.supervisor_feedback}"
    )

    return build_inspection_response(insp)

def calculate_haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

@router.get("/{inspection_id}/export")
def export_inspection_dossier(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    insp = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")

    facility = insp.facility
    inspector = insp.inspector
    template = insp.template

    findings_data = []
    pass_count = 0
    fail_count = 0
    na_count = 0

    for f in insp.findings:
        if f.status == FindingStatus.PASS:
            pass_count += 1
        elif f.status == FindingStatus.FAIL:
            fail_count += 1
        elif f.status == FindingStatus.NA:
            na_count += 1

        findings_data.append({
            "id": f.id,
            "checklist_item_id": f.checklist_item_id,
            "question_text": f.checklist_item.question_text if f.checklist_item else "",
            "question_type": f.checklist_item.question_type if f.checklist_item else "pass_fail",
            "is_required": f.checklist_item.is_required if f.checklist_item else True,
            "status": f.status,
            "notes": f.notes,
            "photo_url": f.photo_url,
            "gps_lat": f.gps_lat,
            "gps_lng": f.gps_lng,
            "captured_at": f.captured_at.isoformat() if f.captured_at else None
        })

    total_evaluated = pass_count + fail_count
    compliance_score = round((pass_count / total_evaluated * 100), 1) if total_evaluated > 0 else 100.0

    # Geofence validation
    geofence = {
        "verified": False,
        "facility_coords": {"lat": facility.latitude, "lng": facility.longitude} if (facility and facility.latitude) else None,
        "submission_coords": {"lat": insp.submission_lat, "lng": insp.submission_lng} if insp.submission_lat else None,
        "distance_meters": None,
        "threshold_meters": 200.0
    }
    if facility and facility.latitude and facility.longitude and insp.submission_lat and insp.submission_lng:
        dist = calculate_haversine_meters(facility.latitude, facility.longitude, insp.submission_lat, insp.submission_lng)
        geofence["distance_meters"] = round(dist, 1)
        geofence["verified"] = dist <= 200.0

    return {
        "dossier_version": "2.0",
        "generated_at": datetime.utcnow().isoformat(),
        "generated_by": current_user.full_name,
        "inspection": {
            "id": insp.id,
            "status": insp.status,
            "priority": insp.priority,
            "scheduled_date": str(insp.scheduled_date) if insp.scheduled_date else None,
            "submission_notes": insp.submission_notes,
            "submitted_at": insp.submitted_at.isoformat() if insp.submitted_at else None,
            "supervisor_feedback": insp.supervisor_feedback,
            "reviewed_at": insp.reviewed_at.isoformat() if insp.reviewed_at else None,
            "reviewed_by": insp.reviewed_by,
            "created_at": insp.created_at.isoformat() if insp.created_at else None,
        },
        "facility": {
            "id": facility.id if facility else None,
            "name": facility.name if facility else "Unknown",
            "license_no": facility.license_no if facility else None,
            "category": facility.category if facility else None,
            "risk_level": facility.risk_level if facility else None,
            "address": facility.address if facility else None,
            "contact_person": facility.contact_person if facility else None,
            "contact_phone": facility.contact_phone if facility else None,
            "latitude": facility.latitude if facility else None,
            "longitude": facility.longitude if facility else None,
        },
        "inspector": {
            "id": inspector.id if inspector else None,
            "name": inspector.full_name if inspector else "Unassigned",
            "email": inspector.email if inspector else None,
            "badge_number": inspector.badge_number if inspector else None,
        },
        "checklist_template": {
            "id": template.id if template else None,
            "title": template.title if template else None,
            "category": template.category if template else None,
        },
        "compliance_summary": {
            "total_items": len(findings_data),
            "passed": pass_count,
            "failed": fail_count,
            "na": na_count,
            "score_percentage": compliance_score,
            "rating": "CRITICAL" if fail_count >= 3 else ("SATISFACTORY" if fail_count == 0 else "ACTION REQUIRED")
        },
        "geofence": geofence,
        "photos": list(dict.fromkeys([f.photo_url for f in insp.findings if f.photo_url and f.photo_url.strip()])),
        "findings": findings_data
    }

