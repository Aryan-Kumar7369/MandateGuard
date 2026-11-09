from datetime import datetime, timedelta, timezone
from app.schemas.mandate import MandateSchema
from app.services.delegation_service import DelegationService

def get_parent_mandate() -> MandateSchema:
    return MandateSchema(
        cumulative_budget=500.00,
        approval_threshold=100.00,
        expiry=datetime.now(timezone.utc) + timedelta(days=5),
        allowed_categories=["electronics", "software"],
        merchant_constraints={"allow": ["Amazon", "GitHub"], "deny": ["UnknownStore"]}
    )

def test_valid_delegation_narrowing():
    parent = get_parent_mandate()
    child = MandateSchema(
        cumulative_budget=200.00,
        approval_threshold=50.00,
        expiry=datetime.now(timezone.utc) + timedelta(days=2),
        allowed_categories=["software"],
        merchant_constraints={"allow": ["GitHub"], "deny": []}
    )
    is_valid, reason = DelegationService.validate_sub_mandate(parent, child)
    assert is_valid is True

def test_invalid_delegation_budget_expansion():
    parent = get_parent_mandate()
    child = MandateSchema(
        cumulative_budget=600.00,
        approval_threshold=50.00,
        expiry=datetime.now(timezone.utc) + timedelta(days=2),
        allowed_categories=["software"],
        merchant_constraints={"allow": ["GitHub"], "deny": []}
    )
    is_valid, reason = DelegationService.validate_sub_mandate(parent, child)
    assert is_valid is False
    assert "exceeds parent budget" in reason

def test_invalid_delegation_category_expansion():
    parent = get_parent_mandate()
    child = MandateSchema(
        cumulative_budget=200.00,
        approval_threshold=50.00,
        expiry=datetime.now(timezone.utc) + timedelta(days=2),
        allowed_categories=["software", "travel"],
        merchant_constraints={"allow": ["GitHub"], "deny": []}
    )
    is_valid, reason = DelegationService.validate_sub_mandate(parent, child)
    assert is_valid is False
    assert "unauthorized categories" in reason