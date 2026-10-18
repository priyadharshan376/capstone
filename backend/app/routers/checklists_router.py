from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ChecklistTemplate, ChecklistItem, User, UserRole
from app.schemas import ChecklistTemplateCreate, ChecklistTemplateResponse
from app.auth import get_current_user, require_role, log_audit_event

router = APIRouter(prefix="/checklists", tags=["Checklists"])

@router.get("", response_model=List[ChecklistTemplateResponse])
def get_checklist_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ChecklistTemplate).all()

@router.get("/{template_id}", response_model=ChecklistTemplateResponse)
def get_checklist_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    template = db.query(ChecklistTemplate).filter(ChecklistTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Checklist template not found")
    return template

@router.post("", response_model=ChecklistTemplateResponse)
def create_checklist_template(
    template_in: ChecklistTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR]))
):
    template = ChecklistTemplate(
        title=template_in.title,
        category=template_in.category,
        description=template_in.description
    )
    db.add(template)
    db.flush()

    for item in template_in.items:
        chk_item = ChecklistItem(
            template_id=template.id,
            question_text=item.question_text,
            question_type=item.question_type,
            is_required=item.is_required,
            order_index=item.order_index
        )
        db.add(chk_item)

    db.commit()
    db.refresh(template)

    log_audit_event(
        db=db,
        event_type="CHECKLIST_TEMPLATE_CREATED",
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        entity_type="ChecklistTemplate",
        entity_id=template.id,
        details=f"Created template '{template.title}' with {len(template_in.items)} criteria"
    )

    return template
