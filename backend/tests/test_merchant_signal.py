from datetime import datetime, timezone
from app.models import Mandate

def test_merchant_signal_valid(db, client):
    mandate = Mandate(
        id="m_sig_valid",
        user_id="u_merchant_1",
        rules={
            "cumulative_budget": 500.0,
            "approval_threshold": 100.0,
            "expiry": datetime.now(timezone.utc).isoformat(),
            "allowed_categories": ["electronics"],
            "merchant_constraints": {"allow": ["Amazon"], "deny": []},
            "allowed_shipping_destinations": []
        },
        signature=None,
        is_revoked=False
    )
    db.add(mandate)
    db.commit()

    res = client.get("/api/v1/merchant/verify-signal/m_sig_valid")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "VALID"
    assert data["within_limits"] is True
    assert data["verification_token"].startswith("v_sig_")

def test_merchant_signal_revoked(db, client):
    mandate = Mandate(
        id="m_sig_revoked",
        user_id="u_merchant_2",
        rules={
            "cumulative_budget": 500.0,
            "approval_threshold": 100.0,
            "expiry": datetime.now(timezone.utc).isoformat(),
            "allowed_categories": ["electronics"],
            "merchant_constraints": {"allow": ["Amazon"], "deny": []},
            "allowed_shipping_destinations": []
        },
        signature=None,
        is_revoked=True
    )
    db.add(mandate)
    db.commit()

    res = client.get("/api/v1/merchant/verify-signal/m_sig_revoked")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "REVOKED"
    assert data["within_limits"] is False