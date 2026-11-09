import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Mandate
from app.schemas.mandate_api import MandateCreateRequest, MandateSignRequest, MandateResponse
from app.services.crypto import CryptoService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/mandates", tags=["Mandates"])

@router.post("/", response_model=MandateResponse, status_code=status.HTTP_201_CREATED)
def create_mandate(request: MandateCreateRequest, db: Session = Depends(get_db)):
    mandate_id = f"mandate_{uuid.uuid4().hex[:12]}"
    rules_dict = request.rules.model_dump(mode="json")
    mandate = Mandate(
        id=mandate_id,
        user_id=request.user_id,
        rules=rules_dict,
        signature=None,
        is_revoked=False
    )
    db.add(mandate)
    db.commit()
    db.refresh(mandate)

    AuditService.record_event(
        db=db,
        event_type="MANDATE_CREATED",
        mandate_id=mandate.id,
        payload={"user_id": mandate.user_id, "rules": rules_dict}
    )

    return mandate

@router.post("/sign", response_model=MandateResponse)
def sign_mandate(request: MandateSignRequest, db: Session = Depends(get_db)):
    mandate = db.query(Mandate).filter(Mandate.id == request.mandate_id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")

    payload = {
        "mandate_id": mandate.id,
        "user_id": mandate.user_id,
        "rules": mandate.rules
    }
    signature = CryptoService.sign_mandate(payload, request.private_key_pem)
    mandate.signature = signature
    db.commit()
    db.refresh(mandate)

    AuditService.record_event(
        db=db,
        event_type="MANDATE_SIGNED",
        mandate_id=mandate.id,
        payload={"signature": signature}
    )

    return mandate

@router.post("/{mandate_id}/revoke", response_model=MandateResponse)
def revoke_mandate(mandate_id: str, db: Session = Depends(get_db)):
    mandate = db.query(Mandate).filter(Mandate.id == mandate_id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")

    mandate.is_revoked = True
    db.commit()
    db.refresh(mandate)

    AuditService.record_event(
        db=db,
        event_type="KILL_SWITCH_REVOCATION",
        mandate_id=mandate.id,
        payload={"is_revoked": True}
    )

    return mandate