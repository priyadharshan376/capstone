from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Facility, User, UserRole
from app.schemas import FacilityCreate, FacilityResponse
from app.auth import get_current_user, require_role, log_audit_event

router = APIRouter(prefix="/facilities", tags=["Facilities"])

@router.get("", response_model=List[FacilityResponse])
def get_facilities(
    category: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Facility)
    if category:
        query = query.filter(Facility.category.ilike(f"%{category}%"))
    if risk_level:
        query = query.filter(Facility.risk_level == risk_level.upper())
    return query.order_by(Facility.name.asc()).all()

@router.get("/{facility_id}", response_model=FacilityResponse)
def get_facility(
    facility_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    fac = db.query(Facility).filter(Facility.id == facility_id).first()
    if not fac:
        raise HTTPException(status_code=404, detail="Facility not found")
    return fac

@router.post("", response_model=FacilityResponse)
def create_facility(
    facility_in: FacilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR]))
):
    existing = db.query(Facility).filter(Facility.license_no == facility_in.license_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="Facility with this license number already exists")

    facility = Facility(
        name=facility_in.name,
        license_no=facility_in.license_no,
        category=facility_in.category,
        address=facility_in.address,
        latitude=facility_in.latitude,
        longitude=facility_in.longitude,
        risk_level=facility_in.risk_level.upper(),
        contact_person=facility_in.contact_person,
        contact_phone=facility_in.contact_phone
    )
    db.add(facility)
    db.commit()
    db.refresh(facility)

    log_audit_event(
        db=db,
        event_type="FACILITY_CREATED",
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        entity_type="Facility",
        entity_id=facility.id,
        details=f"Registered facility '{facility.name}' ({facility.license_no}) with risk level {facility.risk_level}"
    )

    return facility
