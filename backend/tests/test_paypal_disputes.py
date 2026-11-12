import pytest
from decimal import Decimal
from app.models import Mandate, Order, Dispute, Event

def test_paypal_dispute_webhook_ingestion(db, client):
    # Setup test mandate and order
    mandate = Mandate(
        id="m_dispute_test",
        user_id="usr_disp",
        rules={
            "cumulative_budget": 500.0,
            "approval_threshold": 100.0,
            "expiry": "2027-12-31T00:00:00Z",
            "allowed_categories": ["software"],
            "merchant_constraints": {"allow": [], "deny": []},
            "allowed_shipping_destinations": []
        },
        is_revoked=False
    )
    db.add(mandate)
    db.flush()

    order = Order(
        id="ord_disp_test",
        mandate_id="m_dispute_test",
        paypal_order_id="PP_TX_999",
        amount=75.00,
        currency="USD",
        status="CAPTURED",
        payload={"merchant": "GitHub", "category": "software"}
    )
    db.add(order)
    db.commit()

    webhook_payload = {
        "event_type": "PAYMENT.DISPUTE.CREATED",
        "resource": {
            "id": "DISPUTE_PP_001",
            "disputed_transactions": [{"seller_transaction_id": "PP_TX_999"}],
            "dispute_amount": {"value": "75.00", "currency_code": "USD"},
            "reason": "MERCHANDISE_OR_SERVICE_NOT_AS_DESCRIBED"
        }
    }

    res = client.post("/api/v1/disputes/webhook", json=webhook_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "processed"

    # Verify dispute stored in DB
    stored_dispute = db.query(Dispute).filter(Dispute.id == "DISPUTE_PP_001").first()
    assert stored_dispute is not None
    assert float(stored_dispute.amount) == 75.00
    assert stored_dispute.status == "OPEN"

    # Verify audit event recorded
    audit_evt = db.query(Event).filter(Event.event_type == "DISPUTE_CREATED", Event.mandate_id == "m_dispute_test").first()
    assert audit_evt is not None
    assert audit_evt.mandate_id == "m_dispute_test"