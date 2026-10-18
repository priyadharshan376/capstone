import os
import random
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
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
        "created_at": insp.created_at
    }

@router.get("", response_model=List[InspectionResponse])
def get_inspections(
    status: Optional[str] = Query(None),
    inspector_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Inspection)

    # Role-based filtering: Inspector only sees their own assigned inspections
    if current_user.role == UserRole.INSPECTOR:
        query = query.filter(Inspection.inspector_id == current_user.id)
    elif inspector_id:
        query = query.filter(Inspection.inspector_id == inspector_id)

    if status:
        query = query.filter(Inspection.status == status.upper())

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
