from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Mandate, Order
from app.schemas.mandate import MandateSchema, PreFlightDecision
from app.schemas.preflight import PreFlightRequest, PreFlightResponse
from app.services.policy_engine import PolicyEngine
from app.services.intent_drift import IntentDriftDetector
from app.services.audit_service import AuditService
from app.services.velocity_service import VelocityService
from app.services.event_bus import EventBus

router = APIRouter(prefix="/api/v1", tags=["PreFlight"])

@router.post("/preflight", response_model=PreFlightResponse)
async def evaluate_preflight(
    request: PreFlightRequest,
    original_prompt: str | None = None,
    cart_description: str | None = None,
    db: Session = Depends(get_db)
):
    mandate = db.query(Mandate).filter(Mandate.id == request.mandate_id).first()
    if not mandate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mandate '{request.mandate_id}' not found."
        )

    velocity_exceeded, velocity_reason = VelocityService.check_velocity(db, request.mandate_id)
    if velocity_exceeded:
        result = PreFlightResponse(
            decision=PreFlightDecision.ASK_HUMAN,
            reason=f"SECURITY PAUSE: {velocity_reason}",
            mandate_id=request.mandate_id
        )
    else:
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
            db=db,
            signature=mandate.signature,
            current_spent=current_spent
        )

        if result.decision == PreFlightDecision.ALLOW and original_prompt and cart_description:
            drift = IntentDriftDetector.analyze_drift(
                original_prompt=original_prompt,
                cart_description=cart_description,
                item_amount=float(request.amount)
            )
            if drift.suggested_action == PreFlightDecision.ASK_HUMAN:
                result.decision = PreFlightDecision.ASK_HUMAN
                result.reason = f"Intent-Drift Detected: {drift.reasoning}"

    AuditService.record_event(
        db=db,
        event_type="PRE_FLIGHT_CHECK",
        mandate_id=mandate.id,
        payload={
            "amount": float(request.amount),
            "category": request.category,
            "merchant": request.merchant,
            "shipping_destination": request.shipping_destination,
            "decision": result.decision.value,
            "reason": result.reason
        }
    )

    await EventBus.publish(
        event_type="PRE_FLIGHT_EVALUATED",
        payload={
            "mandate_id": mandate.id,
            "decision": result.decision.value,
            "amount": float(request.amount),
            "reason": result.reason
        }
    )

    return result