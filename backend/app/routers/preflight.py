from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Mandate, Order
from app.schemas.mandate import MandateSchema
from app.schemas.preflight import PreFlightRequest, PreFlightResponse
from app.services.policy_engine import PolicyEngine

router = APIRouter(prefix="/api/v1", tags=["PreFlight"])

@router.post("/preflight", response_model=PreFlightResponse)
def evaluate_preflight(
    request: PreFlightRequest,
    db: Session = Depends(get_db)
):
    mandate = db.query(Mandate).filter(Mandate.id == request.mandate_id).first()
    if not mandate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mandate '{request.mandate_id}' not found."
        )

    
    current_spent_result = (
        db.query(func.coalesce(func.sum(Order.amount), 0.0))
        .filter(Order.mandate_id == request.mandate_id, Order.status == "CAPTURED")
        .scalar()
    )
    current_spent = Decimal(str(current_spent_result))

    
    rules_schema = MandateSchema(**mandate.rules)

    
    result = PolicyEngine.evaluate(
        mandate_rules=rules_schema,
        request=request,
        is_revoked=mandate.is_revoked,
        current_spent=current_spent
    )

    return result