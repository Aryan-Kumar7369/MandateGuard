from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models import Dispute, Order, Mandate
from app.services.audit_service import AuditService
from app.services.event_bus import EventBus

router = APIRouter(prefix="/api/v1/disputes", tags=["Disputes"])

class DisputeWebhookPayload(BaseModel):
    event_type: str
    resource: dict

@router.post("/webhook", status_code=200)
async def paypal_dispute_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handles live PayPal Sandbox Dispute webhooks.
    Listens for PAYMENT.DISPUTE.CREATED and PAYMENT.DISPUTE.RESOLVED.
    """
    body = await request.json()
    event_type = body.get("event_type")
    resource = body.get("resource", {})

    dispute_id = resource.get("dispute_id") or resource.get("id", "DISPUTE_UNKNOWN")
    disputed_tx = resource.get("disputed_transactions", [{}])[0]
    paypal_order_id = disputed_tx.get("seller_transaction_id") or resource.get("seller_transaction_id")
    amount_dict = resource.get("dispute_amount", {})
    amount_val = Decimal(str(amount_dict.get("value", "0.00")))
    reason = resource.get("reason", "UNAUTHORIZED_TRANSACTION")

    order = db.query(Order).filter(Order.paypal_order_id == paypal_order_id).first() if paypal_order_id else None
    mandate_id = order.mandate_id if order else "UNKNOWN_MANDATE"

    existing_dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()

    if event_type in ["PAYMENT.DISPUTE.CREATED", "SIMULATED.DISPUTE.CREATED"]:
        if not existing_dispute:
            new_dispute = Dispute(
                id=dispute_id,
                order_id=order.id if order else dispute_id,
                mandate_id=mandate_id,
                amount=amount_val,
                reason=reason,
                status="OPEN"
            )
            db.add(new_dispute)
            db.commit()

        AuditService.record_event(
            db=db,
            event_type="DISPUTE_CREATED",
            mandate_id=mandate_id,
            payload={"dispute_id": dispute_id, "amount": float(amount_val), "reason": reason}
        )

        await EventBus.publish("DISPUTE_CREATED", {
            "dispute_id": dispute_id,
            "mandate_id": mandate_id,
            "amount": float(amount_val),
            "reason": reason,
            "status": "OPEN"
        })

    elif event_type in ["PAYMENT.DISPUTE.RESOLVED", "SIMULATED.DISPUTE.RESOLVED"]:
        if existing_dispute:
            existing_dispute.status = "RESOLVED"
            db.commit()

        AuditService.record_event(
            db=db,
            event_type="DISPUTE_RESOLVED",
            mandate_id=mandate_id,
            payload={"dispute_id": dispute_id, "status": "RESOLVED"}
        )

        await EventBus.publish("DISPUTE_RESOLVED", {
            "dispute_id": dispute_id,
            "mandate_id": mandate_id,
            "status": "RESOLVED"
        })

    return {"status": "processed", "event_type": event_type, "dispute_id": dispute_id}


@router.post("/simulate-event", status_code=201)
async def simulate_dispute_event(
    paypal_order_id: str,
    reason: str = "UNAUTHORIZED_INTENT_DRIFT",
    amount: float = 50.00,
    db: Session = Depends(get_db)
):
    """
    Simulates a PayPal Dispute event locally without needing external webhook tunneling.
    """
    simulated_payload = {
        "event_type": "SIMULATED.DISPUTE.CREATED",
        "resource": {
            "id": f"DISPUTE_SIM_{int(Decimal(amount))}",
            "disputed_transactions": [{"seller_transaction_id": paypal_order_id}],
            "dispute_amount": {"value": str(amount), "currency_code": "USD"},
            "reason": reason
        }
    }

    req_mock = Request(scope={"type": "http"})
    async def json_body():
        return simulated_payload
    req_mock.json = json_body

    return await paypal_dispute_webhook(request=req_mock, db=db)