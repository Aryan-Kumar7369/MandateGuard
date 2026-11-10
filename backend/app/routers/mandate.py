import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Mandate
from app.schemas.mandate import MandateCreateRequest, MandateResponse, MandateSchema
from app.services.crypto import CryptoService
from app.services.audit_service import AuditService
from app.services.event_bus import EventBus
from app.services.llm_mandate_parser import LLMMandateParser

router = APIRouter(prefix="/api/v1/mandates", tags=["Mandates"])

class LLMParseRequest(BaseModel):
    prompt: str

class LLMParseResponse(BaseModel):
    proposed_rules: MandateSchema
    requires_human_confirmation: bool = True

@router.post("/parse-prompt", response_model=LLMParseResponse)
def parse_mandate_prompt(request: LLMParseRequest):
    proposed_rules = LLMMandateParser.parse_natural_language_prompt(request.prompt)
    return LLMParseResponse(
        proposed_rules=proposed_rules,
        requires_human_confirmation=True
    )

@router.post("/", response_model=MandateResponse, status_code=status.HTTP_201_CREATED)
async def create_mandate(
    request: MandateCreateRequest,
    private_key_pem: str | None = None,
    db: Session = Depends(get_db)
):
    mandate_id = f"m_{uuid.uuid4().hex[:12]}"
    rules_dict = request.rules.model_dump(mode="json")
    signature = None

    if private_key_pem:
        signature = CryptoService.sign_mandate(
            payload={"mandate_id": mandate_id, "rules": rules_dict},
            private_key_pem=private_key_pem
        )

    db_mandate = Mandate(
        id=mandate_id,
        user_id=request.user_id,
        rules=rules_dict,
        signature=signature,
        is_revoked=False
    )
    db.add(db_mandate)
    db.commit()
    db.refresh(db_mandate)

    AuditService.record_event(
        db=db,
        event_type="MANDATE_CREATED",
        mandate_id=db_mandate.id,
        payload={"user_id": request.user_id, "rules": rules_dict}
    )

    await EventBus.publish(
        event_type="MANDATE_CREATED",
        payload={"mandate_id": db_mandate.id, "user_id": request.user_id}
    )

    return MandateResponse(
        id=db_mandate.id,
        user_id=db_mandate.user_id,
        rules=MandateSchema(**db_mandate.rules),
        signature=db_mandate.signature,
        is_revoked=db_mandate.is_revoked,
        created_at=db_mandate.created_at
    )

@router.get("/{mandate_id}", response_model=MandateResponse)
def get_mandate(mandate_id: str, db: Session = Depends(get_db)):
    mandate = db.query(Mandate).filter(Mandate.id == mandate_id).first()
    if not mandate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mandate '{mandate_id}' not found."
        )
    return MandateResponse(
        id=mandate.id,
        user_id=mandate.user_id,
        rules=MandateSchema(**mandate.rules),
        signature=mandate.signature,
        is_revoked=mandate.is_revoked,
        created_at=mandate.created_at
    )

@router.post("/{mandate_id}/revoke", response_model=MandateResponse)
async def revoke_mandate(mandate_id: str, db: Session = Depends(get_db)):
    mandate = db.query(Mandate).filter(Mandate.id == mandate_id).first()
    if not mandate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mandate '{mandate_id}' not found."
        )

    mandate.is_revoked = True
    db.commit()
    db.refresh(mandate)

    AuditService.record_event(
        db=db,
        event_type="MANDATE_REVOKED",
        mandate_id=mandate.id,
        payload={"revoked_by": "user_kill_switch"}
    )

    await EventBus.publish(
        event_type="MANDATE_REVOKED",
        payload={"mandate_id": mandate.id, "revoked_at": mandate.created_at.isoformat()}
    )

    return MandateResponse(
        id=mandate.id,
        user_id=mandate.user_id,
        rules=MandateSchema(**mandate.rules),
        signature=mandate.signature,
        is_revoked=mandate.is_revoked,
        created_at=mandate.created_at
    )