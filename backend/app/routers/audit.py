from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/audit", tags=["Audit Log"])

class AuditVerifyResponse(BaseModel):
    is_valid: bool
    message: str
    total_events_verified: int

@router.get("/verify", response_model=AuditVerifyResponse)
def verify_audit_log(db: Session = Depends(get_db)):
    is_valid, message, verified_count = AuditService.verify_chain(db)
    return AuditVerifyResponse(
        is_valid=is_valid,
        message=message,
        total_events_verified=verified_count
    )