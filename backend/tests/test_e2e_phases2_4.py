import time
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.models import Mandate, Delegation, Order, Event, Dispute
from app.schemas.mandate import MandateSchema, PreFlightDecision
from app.schemas.preflight import PreFlightRequest
from app.services.policy_engine import PolicyEngine
from app.services.delegation_service import DelegationService
from app.services.audit_service import AuditService
from app.services.crypto import CryptoService
from app.services.intent_drift import IntentDriftDetector

def test_e2e_happy_path_delegation_to_capture(db, client):
    db.query(Dispute).delete()
    db.query(Event).delete()
    db.query(Order).delete()
    db.query(Delegation).delete()
    db.query(Mandate).delete()
    db.commit()

    now = datetime.now(timezone.utc)
    
    root_mandate = Mandate(
        id="m_e2e_root",
        user_id="user_corp_admin",
        rules={
            "cumulative_budget": 1000.0,
            "approval_threshold": 300.0,
            "expiry": (now + timedelta(days=10)).isoformat(),
            "allowed_categories": ["software", "cloud", "electronics"],
            "merchant_constraints": {"allow": ["GitHub", "AWS", "Amazon"], "deny": []},
            "allowed_shipping_destinations": ["US"]
        },
        signature=None,
        is_revoked=False
    )
    db.add(root_mandate)
    db.commit()

    child_rules = MandateSchema(
        cumulative_budget=Decimal("300.00"),
        approval_threshold=Decimal("100.00"),
        expiry=now + timedelta(days=3),
        allowed_categories=["software"],
        merchant_constraints={"allow": ["GitHub"], "deny": []},
        allowed_shipping_destinations=["US"]
    )

    is_narrowed, msg = DelegationService.validate_sub_mandate(
        MandateSchema(**root_mandate.rules),
        child_rules
    )
    assert is_narrowed is True

    child_mandate = Mandate(
        id="m_e2e_child",
        user_id="user_corp_admin",
        rules=child_rules.model_dump(mode="json"),
        signature=None,
        is_revoked=False
    )
    db.add(child_mandate)
    db.flush()

    delegation = Delegation(
        id="del_e2e_01",
        parent_mandate_id="m_e2e_root",
        child_mandate_id="m_e2e_child",
        delegated_by="agent_root",
        delegated_to="agent_devops"
    )
    db.add(delegation)
    db.commit()

    chain_ok, chain_msg, broken = DelegationService.validate_full_chain(db, "m_e2e_child")
    assert chain_ok is True

    pf_req = PreFlightRequest(
        mandate_id="m_e2e_child",
        amount=Decimal("49.00"),
        category="software",
        merchant="GitHub",
        shipping_destination="US"
    )
    pf_res = PolicyEngine.evaluate(
        mandate_rules=child_rules,
        request=pf_req,
        is_revoked=False,
        db=db
    )
    assert pf_res.decision == PreFlightDecision.ALLOW

    with patch("app.services.paypal_service.PayPalService.get_order_details") as mock_details, \
         patch("app.services.paypal_service.PayPalService.capture_order") as mock_capture:
        
        mock_details.return_value = {
            "id": "PAYPAL_E2E_999",
            "status": "APPROVED",
            "amount": Decimal("49.00"),
            "currency": "USD"
        }
        mock_capture.return_value = {"status": "COMPLETED", "id": "PAYPAL_E2E_999"}

        response = client.post(
            "/api/v1/checkout/execute",
            json={
                "mandate_id": "m_e2e_child",
                "paypal_order_id": "PAYPAL_E2E_999",
                "category": "software",
                "merchant": "GitHub"
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == "CAPTURED"

    is_valid_audit, audit_msg, count = AuditService.verify_chain(db)
    assert is_valid_audit is True
    assert count >= 1


def test_e2e_edge_case_revoked_root_in_3tier_chain(db):
    now = datetime.now(timezone.utc)

    m1 = Mandate(
        id="m_tier1",
        user_id="u1",
        rules={
            "cumulative_budget": 1000.0,
            "approval_threshold": 500.0,
            "expiry": (now + timedelta(days=10)).isoformat(),
            "allowed_categories": ["electronics"],
            "merchant_constraints": {"allow": ["Amazon"], "deny": []},
            "allowed_shipping_destinations": ["US"]
        },
        signature=None,
        is_revoked=True
    )
    m2 = Mandate(
        id="m_tier2",
        user_id="u1",
        rules={
            "cumulative_budget": 500.0,
            "approval_threshold": 250.0,
            "expiry": (now + timedelta(days=5)).isoformat(),
            "allowed_categories": ["electronics"],
            "merchant_constraints": {"allow": ["Amazon"], "deny": []},
            "allowed_shipping_destinations": ["US"]
        },
        signature=None,
        is_revoked=False
    )
    m3 = Mandate(
        id="m_tier3",
        user_id="u1",
        rules={
            "cumulative_budget": 200.0,
            "approval_threshold": 100.0,
            "expiry": (now + timedelta(days=2)).isoformat(),
            "allowed_categories": ["electronics"],
            "merchant_constraints": {"allow": ["Amazon"], "deny": []},
            "allowed_shipping_destinations": ["US"]
        },
        signature=None,
        is_revoked=False
    )
    db.add_all([m1, m2, m3])
    db.flush()

    d1 = Delegation(id="d_t1_t2", parent_mandate_id="m_tier1", child_mandate_id="m_tier2", delegated_by="a1", delegated_to="a2")
    d2 = Delegation(id="d_t2_t3", parent_mandate_id="m_tier2", child_mandate_id="m_tier3", delegated_by="a2", delegated_to="a3")
    db.add_all([d1, d2])
    db.commit()

    is_valid, reason, broken_link = DelegationService.validate_full_chain(db, "m_tier3")
    assert is_valid is False
    assert broken_link == "m_tier1"
    assert "revoked" in reason.lower()


def test_e2e_edge_case_unauthorized_shipping_destination(db):
    now = datetime.now(timezone.utc)
    mandate_rules = MandateSchema(
        cumulative_budget=Decimal("500.00"),
        approval_threshold=Decimal("200.00"),
        expiry=now + timedelta(days=5),
        allowed_categories=["electronics"],
        merchant_constraints={"allow": ["Amazon"], "deny": []},
        allowed_shipping_destinations=["US", "CA"]
    )

    req = PreFlightRequest(
        mandate_id="m_shipping_test",
        amount=Decimal("150.00"),
        category="electronics",
        merchant="Amazon",
        shipping_destination="UK"
    )

    result = PolicyEngine.evaluate(
        mandate_rules=mandate_rules,
        request=req,
        is_revoked=False
    )
    assert result.decision == PreFlightDecision.BLOCK
    assert "Shipping destination 'UK' is not authorized" in result.reason


def test_e2e_edge_case_budget_exhaustion_multi_tx(db):
    now = datetime.now(timezone.utc)
    mandate_rules = MandateSchema(
        cumulative_budget=Decimal("100.00"),
        approval_threshold=Decimal("100.00"),
        expiry=now + timedelta(days=5),
        allowed_categories=["electronics"],
        merchant_constraints={"allow": ["Amazon"], "deny": []},
        allowed_shipping_destinations=[]
    )

    req1 = PreFlightRequest(
        mandate_id="m_budget_exhaust",
        amount=Decimal("90.00"),
        category="electronics",
        merchant="Amazon"
    )
    res1 = PolicyEngine.evaluate(
        mandate_rules=mandate_rules,
        request=req1,
        is_revoked=False,
        current_spent=Decimal("0.00")
    )
    assert res1.decision == PreFlightDecision.ALLOW

    req2 = PreFlightRequest(
        mandate_id="m_budget_exhaust",
        amount=Decimal("20.00"),
        category="electronics",
        merchant="Amazon"
    )
    res2 = PolicyEngine.evaluate(
        mandate_rules=mandate_rules,
        request=req2,
        is_revoked=False,
        current_spent=Decimal("90.00")
    )
    assert res2.decision == PreFlightDecision.BLOCK
    assert "exceeds cumulative budget" in res2.reason


def test_e2e_preflight_p95_latency_benchmark():
    now = datetime.now(timezone.utc)
    mandate_rules = MandateSchema(
        cumulative_budget=Decimal("1000.00"),
        approval_threshold=Decimal("200.00"),
        expiry=now + timedelta(days=10),
        allowed_categories=["electronics", "software"],
        merchant_constraints={"allow": ["Amazon", "GitHub"], "deny": ["BadVendor"]},
        allowed_shipping_destinations=["US"]
    )

    req = PreFlightRequest(
        mandate_id="m_benchmark",
        amount=Decimal("50.00"),
        category="electronics",
        merchant="Amazon",
        shipping_destination="US"
    )

    latencies_ms = []
    iterations = 200

    for _ in range(iterations):
        start = time.perf_counter()
        PolicyEngine.evaluate(mandate_rules=mandate_rules, request=req, is_revoked=False)
        latencies_ms.append((time.perf_counter() - start) * 1000.0)

    latencies_ms.sort()
    p95_index = int(iterations * 0.95)
    p95_latency = latencies_ms[p95_index]

    print(f"\n[BENCHMARK] Policy Engine Pre-flight p95 Latency: {p95_latency:.4f} ms")
    assert p95_latency < 5.0