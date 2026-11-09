from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.schemas.mandate import MandateSchema, PreFlightDecision
from app.schemas.preflight import PreFlightRequest
from app.services.policy_engine import PolicyEngine

def get_base_mandate() -> MandateSchema:
    return MandateSchema(
        cumulative_budget=500.00,
        approval_threshold=100.00,
        expiry=datetime.now(timezone.utc) + timedelta(days=1),
        allowed_categories=["electronics", "software"],
        merchant_constraints={"allow": ["Amazon", "GitHub"], "deny": ["UnknownStore"]}
    )

def test_policy_allow():
    rules = get_base_mandate()
    request = PreFlightRequest(
        mandate_id="m_123",
        amount=Decimal("50.00"),
        category="electronics",
        merchant="Amazon"
    )
    response = PolicyEngine.evaluate(rules, request, is_revoked=False)
    assert response.decision == PreFlightDecision.ALLOW

def test_policy_ask_human_threshold():
    rules = get_base_mandate()
    request = PreFlightRequest(
        mandate_id="m_123",
        amount=Decimal("150.00"),
        category="electronics",
        merchant="Amazon"
    )
    response = PolicyEngine.evaluate(rules, request, is_revoked=False)
    assert response.decision == PreFlightDecision.ASK_HUMAN

def test_policy_block_revoked():
    rules = get_base_mandate()
    request = PreFlightRequest(
        mandate_id="m_123",
        amount=Decimal("50.00"),
        category="electronics",
        merchant="Amazon"
    )
    response = PolicyEngine.evaluate(rules, request, is_revoked=True)
    assert response.decision == PreFlightDecision.BLOCK
    assert "revoked" in response.reason.lower()

def test_policy_block_category():
    rules = get_base_mandate()
    request = PreFlightRequest(
        mandate_id="m_123",
        amount=Decimal("50.00"),
        category="gambling",
        merchant="Amazon"
    )
    response = PolicyEngine.evaluate(rules, request, is_revoked=False)
    assert response.decision == PreFlightDecision.BLOCK

def test_policy_block_budget():
    rules = get_base_mandate()
    request = PreFlightRequest(
        mandate_id="m_123",
        amount=Decimal("450.00"),
        category="electronics",
        merchant="Amazon"
    )
    
    response = PolicyEngine.evaluate(rules, request, is_revoked=False, current_spent=Decimal("100.00"))
    assert response.decision == PreFlightDecision.BLOCK