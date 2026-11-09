import hashlib
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Mandate

router = APIRouter(prefix="/api/v1/merchant", tags=["Merchant Signal"])

class MerchantVerificationResponse(BaseModel):
    mandate_id: str
    status: str
    within_limits: bool
    verification_token: str

@router.get("/verify-signal/{mandate_id}", response_model=MerchantVerificationResponse)
def verify_merchant_signal(mandate_id: str, db: Session = Depends(get_db)):
    mandate = db.query(Mandate).filter(Mandate.id == mandate_id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found.")

    is_valid = not mandate.is_revoked
    raw_token = f"{mandate.id}:{mandate.is_revoked}:{mandate.user_id}"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    return MerchantVerificationResponse(
        mandate_id=mandate.id,
        status="VALID" if is_valid else "REVOKED",
        within_limits=is_valid,
        verification_token=f"v_sig_{token_hash[:16]}"
    )