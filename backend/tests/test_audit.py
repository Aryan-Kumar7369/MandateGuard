from datetime import datetime, timezone
from app.models import Mandate, Event
from app.services.audit_service import AuditService

def create_test_mandate(db, mandate_id: str) -> Mandate:
    mandate = Mandate(
        id=mandate_id,
        user_id="user_test",
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
    return mandate

def test_audit_event_hash_chaining(db):
    db.query(Event).delete()
    db.commit()

    create_test_mandate(db, "m_100")
    
    e1 = AuditService.record_event(
        db=db,
        event_type="MANDATE_CREATED",
        mandate_id="m_100",
        payload={"budget": 500.0}
    )
    assert e1.previous_hash == AuditService.GENESIS_HASH

    e2 = AuditService.record_event(
        db=db,
        event_type="PRE_FLIGHT_CHECK",
        mandate_id="m_100",
        payload={"amount": 50.0, "decision": "ALLOW"}
    )
    assert e2.previous_hash == e1.current_hash

    is_valid, message, count = AuditService.verify_chain(db)
    assert is_valid is True
    assert count >= 2

def test_audit_tamper_detection(db):
    db.query(Event).delete()
    db.commit()

    create_test_mandate(db, "m_200")
    
    e1 = AuditService.record_event(
        db=db,
        event_type="MANDATE_CREATED",
        mandate_id="m_200",
        payload={"budget": 500.0}
    )
    e2 = AuditService.record_event(
        db=db,
        event_type="PRE_FLIGHT_CHECK",
        mandate_id="m_200",
        payload={"amount": 50.0, "decision": "ALLOW"}
    )

    e1.payload = {"budget": 999999.0}
    db.commit()

    is_valid, message, count = AuditService.verify_chain(db)
    assert is_valid is False
    assert "Tamper detected" in message