from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from app.models import Mandate, Order

def create_disputed_mandate_and_order(db):
    mandate = Mandate(
        id="mandate_disp_1",
        user_id="user_disp_test",
        rules={
            "cumulative_budget": 500.0,
            "approval_threshold": 100.0,
            "expiry": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "allowed_categories": ["electronics"],
            "merchant_constraints": {"allow": ["Amazon"], "deny": []}
        },
        signature=None,
        is_revoked=False
    )
    db.add(mandate)

    order = Order(
        id="ord_disp_1",
        paypal_order_id="PAYPAL_TX_999",
        mandate_id="mandate_disp_1",
        amount=75.0,
        currency="USD",
        status="CAPTURED",
        payload={"category": "electronics", "merchant": "Amazon"}
    )
    db.add(order)
    db.commit()

@patch("app.services.paypal_service.PayPalService.list_disputes")
def test_sync_disputes_updates_order_and_audit(mock_list, db, client):
    create_disputed_mandate_and_order(db)

    mock_list.return_value = {
        "items": [
            {
                "dispute_id": "DP-12345",
                "status": "OPEN",
                "reason": "UNAUTHORIZED",
                "dispute_amount": {"value": "75.00", "currency_code": "USD"},
                "disputed_transactions": [
                    {"seller_transaction_id": "PAYPAL_TX_999"}
                ]
            }
        ]
    }

    response = client.post("/api/v1/disputes/sync")
    assert response.status_code == 200

    data = response.json()
    assert data["synced_count"] == 1
    assert data["disputes"][0]["dispute_id"] == "DP-12345"

    updated_order = db.query(Order).filter(Order.id == "ord_disp_1").first()
    assert updated_order.status == "DISPUTED_OPEN"