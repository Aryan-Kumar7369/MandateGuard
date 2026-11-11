import pytest
from app.models import Mandate

def test_merchant_verify_signal_success(db, client):
    mandate = Mandate(
        id="m_merch_test",
        user_id="usr_merch",
        rules={
            "cumulative_budget": 500.0,
            "approval_threshold": 100.0,
            "expiry": "2027-12-31T00:00:00Z",
            "allowed_categories": ["software"],
            "merchant_constraints": {"allow": ["GitHub"], "deny": []},
            "allowed_shipping_destinations": ["US"]
        },
        is_revoked=False
    )
    db.add(mandate)
    db.commit()

    req = {
        "mandate_id": "m_merch_test",
        "amount": 50.0,
        "merchant": "GitHub",
        "category": "software"
    }

    res = client.post("/api/v1/merchant/verify-signal", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["badge_status"] == "VERIFIED_MANDATE"
    assert data["remaining_budget"] == 500.0

def test_merchant_verify_signal_denied_merchant(db, client):
    mandate = Mandate(
        id="m_merch_deny",
        user_id="usr_merch",
        rules={
            "cumulative_budget": 500.0,
            "approval_threshold": 100.0,
            "expiry": "2027-12-31T00:00:00Z",
            "allowed_categories": ["software"],
            "merchant_constraints": {"allow": [], "deny": ["BadVendor"]},
            "allowed_shipping_destinations": ["US"]
        },
        is_revoked=False
    )
    db.add(mandate)
    db.commit()

    req = {
        "mandate_id": "m_merch_deny",
        "amount": 50.0,
        "merchant": "BadVendor",
        "category": "software"
    }

    res = client.post("/api/v1/merchant/verify-signal", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is False
    assert data["badge_status"] == "MERCHANT_DENIED"