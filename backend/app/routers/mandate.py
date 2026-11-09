import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Mandate
from app.schemas.mandate_api import MandateCreateRequest, MandateSignRequest, MandateResponse
from app.services.crypto import CryptoService

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
    return mandate