import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Mandate, Delegation
from app.schemas.mandate import MandateSchema
from app.schemas.delegation import DelegationCreateRequest, DelegationResponse
from app.services.delegation_service import DelegationService

router = APIRouter(prefix="/api/v1/delegations", tags=["Delegations"])


class DelegationNodeResponse(BaseModel):
    mandate_id: str
    user_id: str
    is_revoked: bool
    cumulative_budget: float
    allowed_categories: list[str]
    parent_mandate_id: str | None = None
    delegated_to: str | None = None
    children: list["DelegationNodeResponse"] = []


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


@router.get("/tree/{mandate_id}", response_model=DelegationNodeResponse)
def get_delegation_tree(mandate_id: str, db: Session = Depends(get_db)):
    def build_node(current_id: str, parent_id: str | None = None) -> DelegationNodeResponse:
        m = db.query(Mandate).filter(Mandate.id == current_id).first()
        if not m:
            raise HTTPException(status_code=404, detail=f"Mandate '{current_id}' not found.")

        rules = MandateSchema(**m.rules)
        child_delegations = db.query(Delegation).filter(Delegation.parent_mandate_id == current_id).all()

        child_nodes = [
            build_node(d.child_mandate_id, parent_id=current_id)
            for d in child_delegations
        ]

        return DelegationNodeResponse(
            mandate_id=m.id,
            user_id=m.user_id,
            is_revoked=m.is_revoked,
            cumulative_budget=float(rules.cumulative_budget),
            allowed_categories=rules.allowed_categories,
            parent_mandate_id=parent_id,
            children=child_nodes
        )

    return build_node(mandate_id)