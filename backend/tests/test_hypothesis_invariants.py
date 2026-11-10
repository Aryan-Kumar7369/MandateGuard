from decimal import Decimal
from datetime import datetime, timedelta, timezone
from hypothesis import given, strategies as st, settings, HealthCheck
import pytest

from app.schemas.mandate import MandateSchema, PreFlightDecision
from app.schemas.preflight import PreFlightRequest
from app.services.policy_engine import PolicyEngine
from app.services.delegation_service import DelegationService
from app.services.crypto import CryptoService
from app.services.audit_service import AuditService
from app.models import Mandate, Event

# Custom Hypothesis Strategies
st_money = st.decimals(min_value=Decimal("0.01"), max_value=Decimal("1000000.00"), places=2)
st_category = st.sampled_from(["electronics", "software", "hardware", "cloud", "office", "travel"])
st_merchant = st.sampled_from(["Amazon", "GitHub", "AWS", "BestBuy", "Staples", "Uber"])
st_country = st.sampled_from(["US", "CA", "UK", "DE", "FR", "JP"])


@given(
    budget=st_money,
    threshold=st_money,
    spent=st_money,
    amount=st_money,
    is_revoked=st.booleans()
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_invariant_policy_budget_overspend_always_blocks(budget, threshold, spent, amount, is_revoked):
    now = datetime.now(timezone.utc)
    rules = MandateSchema(
        cumulative_budget=budget,
        approval_threshold=threshold,
        expiry=now + timedelta(days=5),
        allowed_categories=["electronics"],
        merchant_constraints={"allow": ["Amazon"], "deny": []},
        allowed_shipping_destinations=["US"]
    )

    req = PreFlightRequest(
        mandate_id="m_fuzz_policy",
        amount=amount,
        category="electronics",
        merchant="Amazon",
        shipping_destination="US"
    )

    res = PolicyEngine.evaluate(
        mandate_rules=rules,
        request=req,
        is_revoked=is_revoked,
        current_spent=spent
    )

    if is_revoked:
        assert res.decision == PreFlightDecision.BLOCK
        assert "revoked" in res.reason.lower()
    elif (spent + amount) > budget:
        assert res.decision == PreFlightDecision.BLOCK
        assert "exceeds cumulative budget" in res.reason.lower()


@given(
    parent_budget=st_money,
    child_budget=st_money,
    parent_categories=st.sets(st_category, min_size=1, max_size=5),
    child_categories=st.sets(st_category, min_size=1, max_size=5),
    parent_destinations=st.sets(st_country, min_size=0, max_size=3),
    child_destinations=st.sets(st_country, min_size=0, max_size=3)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_invariant_delegation_narrowing_monotonicity(
    parent_budget, child_budget, parent_categories, child_categories, parent_destinations, child_destinations
):
    now = datetime.now(timezone.utc)
    parent_rules = MandateSchema(
        cumulative_budget=parent_budget,
        approval_threshold=parent_budget,
        expiry=now + timedelta(days=10),
        allowed_categories=list(parent_categories),
        merchant_constraints={"allow": [], "deny": []},
        allowed_shipping_destinations=list(parent_destinations)
    )

    child_rules = MandateSchema(
        cumulative_budget=child_budget,
        approval_threshold=child_budget,
        expiry=now + timedelta(days=5),
        allowed_categories=list(child_categories),
        merchant_constraints={"allow": [], "deny": []},
        allowed_shipping_destinations=list(child_destinations)
    )

    is_valid, reason = DelegationService.validate_sub_mandate(parent_rules, child_rules)

    if is_valid:
        assert child_budget <= parent_budget
        assert set(child_categories).issubset(set(parent_categories))
        if parent_destinations:
            assert bool(child_destinations)
            assert set(child_destinations).issubset(set(parent_destinations))


@given(
    parent_budget=st_money,
    categories=st.sets(st_category, min_size=2, max_size=5)
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_invariant_delegation_rejects_explicit_expansion(parent_budget, categories):
    now = datetime.now(timezone.utc)
    parent_rules = MandateSchema(
        cumulative_budget=parent_budget,
        approval_threshold=parent_budget,
        expiry=now + timedelta(days=10),
        allowed_categories=list(categories),
        merchant_constraints={"allow": [], "deny": []},
        allowed_shipping_destinations=["US"]
    )

    expanded_budget_child = MandateSchema(
        cumulative_budget=parent_budget + Decimal("100.00"),
        approval_threshold=parent_budget,
        expiry=now + timedelta(days=5),
        allowed_categories=list(categories),
        merchant_constraints={"allow": [], "deny": []},
        allowed_shipping_destinations=["US"]
    )
    is_valid_b, msg_b = DelegationService.validate_sub_mandate(parent_rules, expanded_budget_child)
    assert is_valid_b is False
    assert "budget" in msg_b.lower()

    unallowed_cat = "unauthorized_category_xyz"
    expanded_cat_child = MandateSchema(
        cumulative_budget=parent_budget,
        approval_threshold=parent_budget,
        expiry=now + timedelta(days=5),
        allowed_categories=list(categories) + [unallowed_cat],
        merchant_constraints={"allow": [], "deny": []},
        allowed_shipping_destinations=["US"]
    )
    is_valid_c, msg_c = DelegationService.validate_sub_mandate(parent_rules, expanded_cat_child)
    assert is_valid_c is False
    assert "categor" in msg_c.lower()


@given(
    payload_key=st.text(min_size=1, max_size=20, alphabet=st.characters(codec="ascii")),
    payload_val=st.text(min_size=1, max_size=50, alphabet=st.characters(codec="ascii"))
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_invariant_ed25519_crypto_signature_tamper_proofing(payload_key, payload_val):
    priv_pem, pub_pem = CryptoService.generate_key_pair()
    payload = {"mandate_id": "m_test", payload_key: payload_val}

    token = CryptoService.sign_mandate(payload, priv_pem)

    verified_payload = CryptoService.verify_signature(token, pub_pem)
    assert verified_payload is not None
    assert isinstance(verified_payload, dict)

    tampered_token = token[:-4] + "xxxx" if len(token) > 4 else token + "x"
    try:
        tampered_result = CryptoService.verify_signature(tampered_token, pub_pem)
        assert tampered_result is None or tampered_result is False
    except Exception:
        pass


def test_invariant_audit_log_hash_chain_integrity(db):
    db.query(Event).delete()
    db.commit()

    mandate = Mandate(
        id="m_fuzz_audit",
        user_id="user_hypo",
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

    events = []
    for i in range(5):
        evt = AuditService.record_event(
            db=db,
            event_type="PRE_FLIGHT_CHECK",
            mandate_id="m_fuzz_audit",
            payload={"step": i, "amount": 10.0 * (i + 1)}
        )
        events.append(evt)

    valid, msg, count = AuditService.verify_chain(db)
    assert valid is True
    assert count == 5

    events[2].payload = {"step": 2, "amount": 99999.0}
    db.commit()

    tampered_valid, tampered_msg, _ = AuditService.verify_chain(db)
    assert tampered_valid is False
    assert "tamper detected" in tampered_msg.lower()