from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# Auth Schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    full_name: str
    role: str
    email: str

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "inspector"
    badge_number: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    badge_number: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Facility Schemas
class FacilityCreate(BaseModel):
    name: str
    license_no: str
    category: str
    address: str
    latitude: float
    longitude: float
    risk_level: str = "MEDIUM"
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None

class FacilityResponse(BaseModel):
    id: int
    name: str
    license_no: str
    category: str
    address: str
    latitude: float
    longitude: float
    risk_level: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Checklist Schemas
class ChecklistItemBase(BaseModel):
    question_text: str
    question_type: str = "pass_fail"
    is_required: bool = True
    order_index: int = 0

class ChecklistItemResponse(ChecklistItemBase):
    id: int
    template_id: int

    class Config:
        from_attributes = True

class ChecklistTemplateCreate(BaseModel):
    title: str
    category: str
    description: Optional[str] = None
    items: List[ChecklistItemBase] = []

class ChecklistTemplateResponse(BaseModel):
    id: int
    title: str
    category: str
    description: Optional[str] = None
    items: List[ChecklistItemResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True

# Findings Schemas
class FindingSubmission(BaseModel):
    checklist_item_id: int
    status: str  # PASS, FAIL, NA
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None

class FindingResponse(BaseModel):
    id: int
    checklist_item_id: int
    question_text: Optional[str] = None
    status: str
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    captured_at: datetime

    class Config:
        from_attributes = True

# Inspection Schemas
class InspectionAssignRequest(BaseModel):
    facility_id: int
    inspector_id: Optional[int] = None
    template_id: int
    scheduled_date: datetime
    priority: str = "NORMAL"

class InspectionSubmissionRequest(BaseModel):
    submission_notes: Optional[str] = None
    submission_lat: float
    submission_lng: float
    findings: List[FindingSubmission]

class SupervisorReviewRequest(BaseModel):
    status: str  # COMPLETED or REJECTED
    supervisor_feedback: str

class InspectionResponse(BaseModel):
    id: int
    facility_id: int
    facility_name: Optional[str] = None
    facility_category: Optional[str] = None
    inspector_id: Optional[int] = None
    inspector_name: Optional[str] = None
    template_id: int
    scheduled_date: datetime
    status: str
    priority: str
    submission_lat: Optional[float] = None
    submission_lng: Optional[float] = None
    submitted_at: Optional[datetime] = None
    supervisor_feedback: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    created_at: datetime
    photos: List[str] = []
    photo_count: int = 0
    findings: List[FindingResponse] = []

    class Config:
        from_attributes = True

class InspectionDetailResponse(InspectionResponse):
    facility: FacilityResponse
    findings: List[FindingResponse] = []

# Audit Event Schema
class AuditEventResponse(BaseModel):
    id: int
    event_type: str
    actor_id: Optional[int] = None
    actor_name: str
    entity_type: str
    entity_id: int
    details: Optional[str] = None
    timestamp: datetime
    hash_signature: Optional[str] = None

    class Config:
        from_attributes = True
