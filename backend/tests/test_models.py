import uuid
from datetime import datetime, timezone
from app.models import Mandate

def test_create_mandate(db):
    mandate_id = str(uuid.uuid4())
    dummy_mandate = Mandate(
        id=mandate_id,
        user_id="user_123",
        rules={
            "cumulative_budget": 500.0,
            "approval_threshold": 100.0,
            "expiry": datetime.now(timezone.utc).isoformat(),
            "allowed_categories": ["electronics"],
            "merchant_constraints": {"allow": ["Amazon"], "deny": []}
        },
        signature=None,
        is_revoked=False
    )
    
    db.add(dummy_mandate)
    db.commit()

    retrieved = db.query(Mandate).filter(Mandate.id == mandate_id).first()
    assert retrieved is not None
    assert retrieved.user_id == "user_123"
    assert retrieved.rules["cumulative_budget"] == 500.0
    assert retrieved.is_revoked is False