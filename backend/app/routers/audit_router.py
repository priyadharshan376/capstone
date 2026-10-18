from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuditEvent, User, UserRole
from app.schemas import AuditEventResponse
from app.auth import get_current_user, require_role

router = APIRouter(prefix="/audit-logs", tags=["Audit Trail"])

@router.get("", response_model=List[AuditEventResponse])
def get_audit_trail(
    limit: int = Query(50, ge=1, le=200),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR]))
):
    """Retrieve immutable audit trail records with tamper-evident cryptographic hash signatures"""
    query = db.query(AuditEvent)
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)

    return query.order_by(AuditEvent.id.desc()).limit(limit).all()

@router.get("/verify-chain")
def verify_audit_chain_integrity(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR]))
):
    """Verifies that all audit events have not been modified or tampered with since creation"""
    import hashlib
    events = db.query(AuditEvent).order_by(AuditEvent.id.asc()).all()
    prev_hash = "GENESIS_BLOCK_000000000000000000"
    is_valid = True
    broken_event_id = None

    for ev in events:
        raw_signature = f"{prev_hash}|{ev.event_type}|{ev.actor_id}|{ev.entity_type}|{ev.entity_id}|{ev.timestamp.isoformat()}|{ev.details}"
        expected_hash = hashlib.sha256(raw_signature.encode()).hexdigest()
        if ev.hash_signature != expected_hash:
            is_valid = False
            broken_event_id = ev.id
            break
        prev_hash = ev.hash_signature

    return {
        "chain_intact": is_valid,
        "total_records_verified": len(events),
        "compromised_record_id": broken_event_id,
        "verification_status": "Tamper-Evident: Integrity Confirmed" if is_valid else "ALERT: Integrity Compromised!"
    }
