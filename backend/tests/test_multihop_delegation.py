from datetime import datetime, timedelta, timezone
from app.models import Mandate, Delegation
from app.services.delegation_service import DelegationService

def test_multihop_chain_valid(db):
    now = datetime.now(timezone.utc)

    root = Mandate(
        id="m_root",
        user_id="user_1",
        rules={
            "cumulative_budget": 1000.0,
            "approval_threshold": 200.0,
            "expiry": (now + timedelta(days=10)).isoformat(),
            "allowed_categories": ["electronics", "software"],
            "merchant_constraints": {"allow": ["Amazon", "GitHub"], "deny": []},
            "allowed_shipping_destinations": ["US"]
        },
        signature=None,
        is_revoked=False
    )

    child = Mandate(
        id="m_child",
        user_id="user_1",
        rules={
            "cumulative_budget": 500.0,
            "approval_threshold": 100.0,
            "expiry": (now + timedelta(days=5)).isoformat(),
            "allowed_categories": ["electronics"],
            "merchant_constraints": {"allow": ["Amazon"], "deny": []},
            "allowed_shipping_destinations": ["US"]
        },
        signature=None,
        is_revoked=False
    )

    subchild = Mandate(
        id="m_subchild",
        user_id="user_1",
        rules={
            "cumulative_budget": 200.0,
            "approval_threshold": 50.0,
            "expiry": (now + timedelta(days=2)).isoformat(),
            "allowed_categories": ["electronics"],
            "merchant_constraints": {"allow": ["Amazon"], "deny": []},
            "allowed_shipping_destinations": ["US"]
        },
        signature=None,
        is_revoked=False
    )

    db.add_all([root, child, subchild])
    db.flush()

    del1 = Delegation(id="d_1", parent_mandate_id="m_root", child_mandate_id="m_child", delegated_by="p_agent", delegated_to="c_agent")
    del2 = Delegation(id="d_2", parent_mandate_id="m_child", child_mandate_id="m_subchild", delegated_by="c_agent", delegated_to="sc_agent")
    db.add_all([del1, del2])
    db.commit()

    is_valid, reason, broken_link = DelegationService.validate_full_chain(db, "m_subchild")
    assert is_valid is True
    assert broken_link is None

def test_multihop_chain_broken_by_revocation(db):
    now = datetime.now(timezone.utc)

    root = Mandate(
        id="m_root_rev",
        user_id="user_1",
        rules={
            "cumulative_budget": 1000.0,
            "approval_threshold": 200.0,
            "expiry": (now + timedelta(days=10)).isoformat(),
            "allowed_categories": ["electronics"],
            "merchant_constraints": {"allow": ["Amazon"], "deny": []},
            "allowed_shipping_destinations": []
        },
        signature=None,
        is_revoked=True
    )

    child = Mandate(
        id="m_child_rev",
        user_id="user_1",
        rules={
            "cumulative_budget": 500.0,
            "approval_threshold": 100.0,
            "expiry": (now + timedelta(days=5)).isoformat(),
            "allowed_categories": ["electronics"],
            "merchant_constraints": {"allow": ["Amazon"], "deny": []},
            "allowed_shipping_destinations": []
        },
        signature=None,
        is_revoked=False
    )

    db.add_all([root, child])
    db.flush()

    del1 = Delegation(id="d_rev_1", parent_mandate_id="m_root_rev", child_mandate_id="m_child_rev", delegated_by="p_agent", delegated_to="c_agent")
    db.add(del1)
    db.commit()

    is_valid, reason, broken_link = DelegationService.validate_full_chain(db, "m_child_rev")
    assert is_valid is False
    assert "revoked" in reason.lower()
    assert broken_link == "m_root_rev"