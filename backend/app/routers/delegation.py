import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Mandate, Delegation
from app.schemas.mandate import MandateSchema
from app.schemas.delegation import DelegationCreateRequest, DelegationResponse
from app.services.delegation_service import DelegationService

router = APIRouter(prefix="/api/v1/delegations", tags=["Delegations"])

@router.post("/", response_model=DelegationResponse, status_code=status.HTTP_201_CREATED)
def create_delegation(request: DelegationCreateRequest, db: Session = Depends(get_db)):
    parent_mandate = db.query(Mandate).filter(Mandate.id == request.parent_mandate_id).first()
    if not parent_mandate:
        raise HTTPException(status_code=404, detail="Parent mandate not found.")

    if parent_mandate.is_revoked:
        raise HTTPException(status_code=400, detail="Cannot delegate from a revoked parent mandate.")

    parent_rules = MandateSchema(**parent_mandate.rules)
    is_valid, reason = DelegationService.validate_sub_mandate(parent_rules, request.child_rules)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid delegation narrowing: {reason}")

    child_mandate_id = f"mandate_{uuid.uuid4().hex[:12]}"
    child_rules_dict = request.child_rules.model_dump(mode="json")
    child_mandate = Mandate(
        id=child_mandate_id,
        user_id=parent_mandate.user_id,
        rules=child_rules_dict,
        signature=None,
        is_revoked=False
    )

    delegation_id = f"del_{uuid.uuid4().hex[:12]}"
    delegation = Delegation(
        id=delegation_id,
        parent_mandate_id=parent_mandate.id,
        child_mandate_id=child_mandate_id,
        delegated_by=request.delegated_by,
        delegated_to=request.delegated_to
    )

    db.add(child_mandate)
    db.add(delegation)
    db.commit()
    db.refresh(delegation)

    return delegation