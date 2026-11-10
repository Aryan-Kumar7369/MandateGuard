import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone

from app.models import Mandate, Event
from app.schemas.mandate import MandateSchema, PreFlightDecision
from app.schemas.preflight import PreFlightRequest
from app.services.policy_engine import PolicyEngine
from app.services.delegation_service import DelegationService
from app.services.audit_service import AuditService
from app.services.llm_mandate_parser import LLMMandateParser
from tests.red_team_corpus import ATTACK_CORPUS


def test_red_team_prompt_injection_safety():
    """Verify that prompt injections cannot extract unlimited budget rules."""
    attack = next(a for a in ATTACK_CORPUS if a["id"] == "ADV_PARSER_01")
    parsed = LLMMandateParser.parse_natural_language_prompt(attack["prompt"])

    
    assert parsed.cumulative_budget <= 1000.0
    assert "*" not in parsed.allowed_categories


def test_red_team_delegation_expansion_attempts():
    """Verify child mandates cannot expand authority beyond parent limits."""
    now = datetime.now(timezone.utc)

    
    p1 = MandateSchema(
        cumulative_budget=Decimal("100.00"),
        approval_threshold=Decimal("50.00"),
        expiry=now + timedelta(days=5),
        allowed_categories=["electronics"],
        merchant_constraints={"allow": [], "deny": []},
        allowed_shipping_destinations=["US"]
    )
    c1 = MandateSchema(
        cumulative_budget=Decimal("500.00"),
        approval_threshold=Decimal("50.00"),
        expiry=now + timedelta(days=2),
        allowed_categories=["electronics"],
        merchant_constraints={"allow": [], "deny": []},
        allowed_shipping_destinations=["US"]
    )
    ok1, msg1 = DelegationService.validate_sub_mandate(p1, c1)
    assert ok1 is False
    assert "exceeds parent budget" in msg1.lower()

    
    p2 = MandateSchema(
        cumulative_budget=Decimal("200.00"),
        approval_threshold=Decimal("50.00"),
        expiry=now + timedelta(days=5),
        allowed_categories=["electronics"],
        merchant_constraints={"allow": [], "deny": ["BadVendor"]},
        allowed_shipping_destinations=["US"]
    )
    c2 = MandateSchema(
        cumulative_budget=Decimal("100.00"),
        approval_threshold=Decimal("50.00"),
        expiry=now + timedelta(days=2),
        allowed_categories=["electronics"],
        merchant_constraints={"allow": ["BadVendor"], "deny": []},
        allowed_shipping_destinations=["US"]
    )
    ok2, msg2 = DelegationService.validate_sub_mandate(p2, c2)
    assert ok2 is False
    assert "denied" in msg2.lower()


def test_red_team_merchant_spoofing_case_and_whitespace():
    """Verify case-insensitive and whitespace-stripped merchant blocking."""
    rules = MandateSchema(
        cumulative_budget=Decimal("500.00"),
        approval_threshold=Decimal("100.00"),
        expiry=datetime.now(timezone.utc) + timedelta(days=5),
        allowed_categories=["electronics"],
        merchant_constraints={"allow": [], "deny": ["BadVendor"]},
        allowed_shipping_destinations=["US"]
    )

    req = PreFlightRequest(
        mandate_id="m_redteam_1",
        amount=Decimal("50.00"),
        category="electronics",
        merchant="  bAdVeNdOr  ",
        shipping_destination="US"
    )

    res = PolicyEngine.evaluate(rules, req, is_revoked=False)
    assert res.decision == PreFlightDecision.BLOCK
    assert "explicitly blocked" in res.reason.lower()


def test_red_team_destination_sql_injection_bypass():
    """Verify malicious shipping destination strings are strictly rejected."""
    rules = MandateSchema(
        cumulative_budget=Decimal("500.00"),
        approval_threshold=Decimal("100.00"),
        expiry=datetime.now(timezone.utc) + timedelta(days=5),
        allowed_categories=["electronics"],
        merchant_constraints={"allow": ["Amazon"], "deny": []},
        allowed_shipping_destinations=["US"]
    )

    req = PreFlightRequest(
        mandate_id="m_redteam_2",
        amount=Decimal("50.00"),
        category="electronics",
        merchant="Amazon",
        shipping_destination="US; DROP TABLE orders; --"
    )

    res = PolicyEngine.evaluate(rules, req, is_revoked=False)
    assert res.decision == PreFlightDecision.BLOCK
    assert "not authorized" in res.reason.lower()


def test_red_team_audit_tampered_payload_detection(db):
    """Verify cryptographic SHA-256 hash-chain flags payload modifications."""
    db.query(Event).delete()
    db.commit()

    mandate = Mandate(
        id="m_rt_audit",
        user_id="u_attacker",
        rules={
            "cumulative_budget": 500.0,
            "approval_threshold": 100.0,
            "expiry": datetime.now(timezone.utc).isoformat(),
            "allowed_categories": ["electronics"],
            "merchant_constraints": {"allow": ["Amazon"], "deny": []},
            "allowed_shipping_destinations": ["US"]
        },
        signature=None,
        is_revoked=False
    )
    db.add(mandate)
    db.commit()

    e1 = AuditService.record_event(db, "MANDATE_CREATED", mandate_id="m_rt_audit", payload={"budget": 500.0})
    e2 = AuditService.record_event(db, "PRE_FLIGHT_CHECK", mandate_id="m_rt_audit", payload={"amount": 50.0, "decision": "ALLOW"})

    
    e1.payload = {"budget": 999999.0}
    db.commit()

    is_valid, msg, count = AuditService.verify_chain(db)
    assert is_valid is False
    assert "tamper detected" in msg.lower()