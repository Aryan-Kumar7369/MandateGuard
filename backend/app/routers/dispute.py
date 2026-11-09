from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Order
from app.schemas.dispute import DisputeSyncResponse, DisputeSummary
from app.services.paypal_service import PayPalService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/disputes", tags=["Disputes"])

@router.post("/sync", response_model=DisputeSyncResponse)
def sync_disputes(db: Session = Depends(get_db)):
    disputes_data = PayPalService.list_disputes()
    items = disputes_data.get("items", [])
    
    synced_disputes: list[DisputeSummary] = []

    for item in items:
        dispute_id = item.get("dispute_id", "")
        status = item.get("status", "UNKNOWN")
        reason = item.get("reason", "UNSPECIFIED")
        
        amount_dict = item.get("dispute_amount", {})
        amount = float(amount_dict.get("value", 0.0))
        currency = amount_dict.get("currency_code", "USD")

        disputed_txs = item.get("disputed_transactions", [])
        paypal_order_id = None
        if disputed_txs:
            paypal_order_id = disputed_txs[0].get("seller_transaction_id") or disputed_txs[0].get("custom_id")

        if paypal_order_id:
            order = db.query(Order).filter(Order.paypal_order_id == paypal_order_id).first()
            if order:
                order.status = f"DISPUTED_{status}"
                db.commit()

                AuditService.record_event(
                    db=db,
                    event_type="DISPUTE_FILED",
                    mandate_id=order.mandate_id,
                    payload={
                        "dispute_id": dispute_id,
                        "paypal_order_id": paypal_order_id,
                        "status": status,
                        "reason": reason,
                        "amount": amount
                    }
                )

        synced_disputes.append(
            DisputeSummary(
                dispute_id=dispute_id,
                status=status,
                reason=reason,
                amount=amount,
                currency=currency,
                paypal_order_id=paypal_order_id
            )
        )

    return DisputeSyncResponse(
        synced_count=len(synced_disputes),
        disputes=synced_disputes
    )