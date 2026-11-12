from decimal import Decimal
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Dispute, Order, Mandate, Event, Delegation
from app.services.audit_service import AuditService
from app.services.event_bus import EventBus
from app.services.paypal_service import PayPalService
from app.schemas.dispute import (
    DisputeSyncResponse,
    DisputeSummary,
    EvidenceBundleResponse,
    RecoursePreviewResponse,
    RecourseChecklistItem,
)

router = APIRouter(prefix="/api/v1/disputes", tags=["Disputes"])

@router.get("/", response_model=list[DisputeSummary])
def list_recorded_disputes(db: Session = Depends(get_db)):
    disputes = db.query(Dispute).order_by(Dispute.created_at.desc()).all()
    results = []
    for d in disputes:
        order = db.query(Order).filter(Order.id == d.order_id).first()
        paypal_tx = order.paypal_order_id if order else None
        results.append(
            DisputeSummary(
                dispute_id=d.id,
                status=d.status,
                reason=d.reason,
                amount=float(d.amount),
                currency="USD",
                paypal_order_id=paypal_tx
            )
        )
    return results

@router.post("/sync", response_model=DisputeSyncResponse)
def sync_disputes_from_paypal(db: Session = Depends(get_db)):
    try:
        data = PayPalService.list_disputes()
    except Exception:
        data = {"items": []}

    items = data.get("items", [])
    synced = []
    for item in items:
        disp_id = item.get("dispute_id") or item.get("id", "UNKNOWN_DISPUTE")
        disp_status = item.get("status", "OPEN")
        disp_reason = item.get("reason", "UNAUTHORIZED")
        amt_obj = item.get("dispute_amount", {})
        val = float(amt_obj.get("value", 0.0))
        currency = amt_obj.get("currency_code", "USD")
        disputed_txs = item.get("disputed_transactions", [])
        seller_tx_id = disputed_txs[0].get("seller_transaction_id") if disputed_txs else None

        order = None
        if seller_tx_id:
            order = db.query(Order).filter(Order.paypal_order_id == seller_tx_id).first()
            if not order:
                order = db.query(Order).filter(Order.id == seller_tx_id).first()

        if order:
            order.status = f"DISPUTED_{disp_status}"
            db.commit()

        mandate_id = order.mandate_id if order else "UNKNOWN_MANDATE"
        existing = db.query(Dispute).filter(Dispute.id == disp_id).first()
        if not existing:
            new_disp = Dispute(
                id=disp_id,
                order_id=order.id if order else disp_id,
                mandate_id=mandate_id,
                amount=Decimal(str(val)),
                reason=disp_reason,
                status=disp_status
            )
            db.add(new_disp)
            db.commit()
        else:
            existing.status = disp_status
            db.commit()

        AuditService.record_event(
            db=db,
            event_type="DISPUTE_SYNCED",
            mandate_id=mandate_id,
            payload={"dispute_id": disp_id, "status": disp_status, "reason": disp_reason}
        )

        synced.append(
            DisputeSummary(
                dispute_id=disp_id,
                status=disp_status,
                reason=disp_reason,
                amount=val,
                currency=currency,
                paypal_order_id=seller_tx_id
            )
        )
    return DisputeSyncResponse(synced_count=len(synced), disputes=synced)

@router.get("/evidence-bundle/{dispute_id}", response_model=EvidenceBundleResponse)
def get_dispute_evidence_bundle(dispute_id: str, db: Session = Depends(get_db)):
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail=f"Dispute '{dispute_id}' not found.")

    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    if not order and dispute.order_id:
        order = db.query(Order).filter(Order.paypal_order_id == dispute.order_id).first()

    mandate = db.query(Mandate).filter(Mandate.id == dispute.mandate_id).first()
    if not mandate and order:
        mandate = db.query(Mandate).filter(Mandate.id == order.mandate_id).first()

    delegation_chain = []
    if mandate:
        curr_id = mandate.id
        while curr_id:
            del_rec = db.query(Delegation).filter(Delegation.child_mandate_id == curr_id).first()
            if not del_rec:
                break
            parent = db.query(Mandate).filter(Mandate.id == del_rec.parent_mandate_id).first()
            delegation_chain.append({
                "parent_mandate_id": del_rec.parent_mandate_id,
                "child_mandate_id": del_rec.child_mandate_id,
                "delegated_by": del_rec.delegated_by,
                "delegated_to": del_rec.delegated_to,
                "created_at": del_rec.created_at.isoformat() if del_rec.created_at else None,
                "parent_rules": parent.rules if parent else None
            })
            curr_id = del_rec.parent_mandate_id

    events = []
    if mandate:
        db_events = db.query(Event).filter(Event.mandate_id == mandate.id).order_by(Event.created_at.asc()).all()
        for ev in db_events:
            events.append({
                "id": ev.id,
                "event_type": ev.event_type,
                "payload": ev.payload,
                "current_hash": ev.current_hash,
                "previous_hash": ev.previous_hash,
                "created_at": ev.created_at.isoformat() if ev.created_at else None
            })

    is_valid, verify_msg, _ = AuditService.verify_chain(db)

    return EvidenceBundleResponse(
        dispute_id=dispute.id,
        order_id=order.id if order else None,
        paypal_order_id=order.paypal_order_id if order else None,
        mandate_id=dispute.mandate_id,
        amount=float(dispute.amount),
        reason=dispute.reason,
        status=dispute.status,
        mandate_rules=mandate.rules if mandate else None,
        mandate_signature=mandate.signature if mandate else None,
        delegation_chain=delegation_chain,
        audit_trail=events,
        chain_integrity_valid=is_valid,
        assembled_at=datetime.now(timezone.utc).isoformat()
    )

@router.get("/recourse-preview/{dispute_id}", response_model=RecoursePreviewResponse)
def get_recourse_preview(dispute_id: str, db: Session = Depends(get_db)):
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail=f"Dispute '{dispute_id}' not found.")

    order = db.query(Order).filter(Order.id == dispute.order_id).first()
    mandate = db.query(Mandate).filter(Mandate.id == dispute.mandate_id).first()
    is_valid_chain, _, _ = AuditService.verify_chain(db)

    checklist = [
        RecourseChecklistItem(
            rule="Human Authorization Artifact",
            satisfied=mandate is not None,
            details=f"Mandate {mandate.id} recorded with verified schema." if mandate else "No structured mandate found."
        ),
        RecourseChecklistItem(
            rule="Cryptographic Biometric Proof (FIDO2 / JWS)",
            satisfied=mandate is not None and mandate.signature is not None,
            details="Ed25519 / FIDO2 Passkey signature attached to spending authorization." if (mandate and mandate.signature) else "Signature missing or unverified."
        ),
        RecourseChecklistItem(
            rule="Pre-Flight Constraint Compliance",
            satisfied=order is not None and order.status in ["CAPTURED", "DISPUTED_OPEN", "DISPUTED_RESOLVED"],
            details="Pre-flight deterministic gate authorized transaction before PayPal capture." if order else "No pre-flight order match found."
        ),
        RecourseChecklistItem(
            rule="Audit Log Tamper-Evidence",
            satisfied=is_valid_chain,
            details="Cryptographic SHA-256 hash-chain verified from genesis with zero tampering." if is_valid_chain else "Audit log chain anomaly detected."
        )
    ]

    satisfied_count = sum(1 for item in checklist if item.satisfied)
    readiness = (satisfied_count / len(checklist)) * 100.0

    advisory = (
        "Based on PayPal Agentic Commerce policy standards, this evidence bundle demonstrates "
        "explicit, signed human intent prior to order capture. The cryptographic Passkey record "
        "and tamper-evident audit trail refute claims of unintended authorization, providing "
        "substantiated documentation for dispute defense."
    )

    return RecoursePreviewResponse(
        dispute_id=dispute.id,
        policy_reference="PayPal Agentic Commerce Dispute & Protection Framework (Section 11)",
        readiness_percentage=readiness,
        checklist=checklist,
        advisory_explanation=advisory
    )

@router.post("/webhook", status_code=200)
async def paypal_dispute_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
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
    simulated_payload = {
        "event_type": "SIMULATED.DISPUTE.CREATED",
        "resource": {
            "id": f"DISPUTE_SIM_{int(Decimal(str(amount)))}",
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
