from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.models import Mandate

def create_active_mandate(db, mandate_id: str) -> Mandate:
    mandate = Mandate(
        id=mandate_id,
        user_id="user_paypal_test",
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
    db.commit()
    return mandate

@patch("app.services.paypal_service.PayPalService.get_order_details")
@patch("app.services.paypal_service.PayPalService.capture_order")
def test_paypal_checkout_allowed(mock_capture, mock_details, db, client):
    create_active_mandate(db, "mandate_pp_1")

    mock_details.return_value = {
        "id": "PAYPAL_ORD_001",
        "status": "APPROVED",
        "amount": Decimal("50.00"),
        "currency": "USD"
    }
    mock_capture.return_value = {"status": "COMPLETED", "id": "PAYPAL_ORD_001"}

    response = client.post(
        "/api/v1/checkout/execute",
        json={
            "mandate_id": "mandate_pp_1",
            "paypal_order_id": "PAYPAL_ORD_001",
            "category": "electronics",
            "merchant": "Amazon"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "ALLOW"
    assert data["status"] == "CAPTURED"
    assert data["paypal_order_id"] == "PAYPAL_ORD_001"

@patch("app.services.paypal_service.PayPalService.get_order_details")
def test_paypal_checkout_blocked_category(mock_details, db, client):
    create_active_mandate(db, "mandate_pp_2")

    mock_details.return_value = {
        "id": "PAYPAL_ORD_002",
        "status": "APPROVED",
        "amount": Decimal("50.00"),
        "currency": "USD"
    }

    response = client.post(
        "/api/v1/checkout/execute",
        json={
            "mandate_id": "mandate_pp_2",
            "paypal_order_id": "PAYPAL_ORD_002",
            "category": "gambling",
            "merchant": "Amazon"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert data["status"] == "BLOCKED"