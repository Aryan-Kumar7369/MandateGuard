from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.schemas.mandate import MandateSchema, PreFlightDecision
from app.schemas.preflight import PreFlightRequest
from app.services.policy_engine import PolicyEngine

def get_base_rules() -> MandateSchema:
    return MandateSchema(
        cumulative_budget=Decimal("500.00"),
        approval_threshold=Decimal("100.00"),
        expiry=datetime.now(timezone.utc) + timedelta(days=1),
        allowed_categories=["electronics"],
        merchant_constraints={"allow": ["Amazon"], "deny": []},
        allowed_shipping_destinations=["US"]
    )

def test_policy_allow():
    rules = get_base_rules()
    req = PreFlightRequest(
        mandate_id="m_1",
        amount=Decimal("50.00"),
        category="electronics",
        merchant="Amazon",
        shipping_destination="US"
    )
    res = PolicyEngine.evaluate(rules, req, is_revoked=False)
    assert res.decision == PreFlightDecision.ALLOW

def test_policy_ask_human_threshold():
    rules = get_base_rules()
    req = PreFlightRequest(
        mandate_id="m_1",
        amount=Decimal("150.00"),
        category="electronics",
        merchant="Amazon",
        shipping_destination="US"
    )
    res = PolicyEngine.evaluate(rules, req, is_revoked=False)
    assert res.decision == PreFlightDecision.ASK_HUMAN

def test_policy_block_category():
    rules = get_base_rules()
    req = PreFlightRequest(
        mandate_id="m_1",
        amount=Decimal("50.00"),
        category="clothing",
        merchant="Amazon",
        shipping_destination="US"
    )
    res = PolicyEngine.evaluate(rules, req, is_revoked=False)
    assert res.decision == PreFlightDecision.BLOCK

def test_policy_block_budget():
    rules = get_base_rules()
    req = PreFlightRequest(
        mandate_id="m_1",
        amount=Decimal("600.00"),
        category="electronics",
        merchant="Amazon",
        shipping_destination="US"
    )
    res = PolicyEngine.evaluate(rules, req, is_revoked=False)
    assert res.decision == PreFlightDecision.BLOCK