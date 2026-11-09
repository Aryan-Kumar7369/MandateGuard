import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Mandate, Order
from app.schemas.mandate import MandateSchema, PreFlightDecision
from app.schemas.preflight import PreFlightRequest
from app.schemas.checkout import CheckoutExecutionRequest, CheckoutExecutionResponse
from app.services.policy_engine import PolicyEngine
from app.services.paypal_service import PayPalService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/checkout", tags=["Checkout"])

@router.post("/execute", response_model=CheckoutExecutionResponse)
def execute_checkout(
    request: CheckoutExecutionRequest,
    db: Session = Depends(get_db)
):
    mandate = db.query(Mandate).filter(Mandate.id == request.mandate_id).first()
    if not mandate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mandate '{request.mandate_id}' not found."
        )

    paypal_order = PayPalService.get_order_details(request.paypal_order_id)
    order_amount = paypal_order["amount"]
    currency = paypal_order["currency"]

    current_spent_result = (
        db.query(func.coalesce(func.sum(Order.amount), 0.0))
        .filter(Order.mandate_id == request.mandate_id, Order.status == "CAPTURED")
        .scalar()
    )
    current_spent = Decimal(str(current_spent_result))

    rules_schema = MandateSchema(**mandate.rules)

    preflight_request = PreFlightRequest(
        mandate_id=request.mandate_id,
        amount=order_amount,
        category=request.category,
        merchant=request.merchant
    )

    evaluation = PolicyEngine.evaluate(
        mandate_rules=rules_schema,
        request=preflight_request,
        is_revoked=mandate.is_revoked,
        signature=mandate.signature,
        current_spent=current_spent
    )

    order_record_id = f"ord_{uuid.uuid4().hex[:12]}"

    if evaluation.decision == PreFlightDecision.ALLOW:
        capture_result = PayPalService.capture_order(request.paypal_order_id)
        order_status = "CAPTURED"
    elif evaluation.decision == PreFlightDecision.ASK_HUMAN:
        order_status = "PENDING_HUMAN_APPROVAL"
    else:
        order_status = "BLOCKED"

    db_order = Order(
        id=order_record_id,
        paypal_order_id=request.paypal_order_id,
        mandate_id=mandate.id,
        amount=float(order_amount),
        currency=currency,
        status=order_status
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    AuditService.record_event(
        db=db,
        event_type="PAYPAL_CHECKOUT_EXECUTION",
        mandate_id=mandate.id,
        payload={
            "order_id": db_order.id,
            "paypal_order_id": request.paypal_order_id,
            "amount": float(order_amount),
            "currency": currency,
            "decision": evaluation.decision.value,
            "status": order_status,
            "reason": evaluation.reason
        }
    )

    return CheckoutExecutionResponse(
        order_id=db_order.id,
        paypal_order_id=request.paypal_order_id,
        decision=evaluation.decision,
        status=order_status,
        amount=order_amount,
        currency=currency,
        reason=evaluation.reason
    )