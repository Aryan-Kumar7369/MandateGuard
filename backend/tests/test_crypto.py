from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.services.crypto import CryptoService
from app.services.policy_engine import PolicyEngine
from app.schemas.mandate import MandateSchema, PreFlightDecision
from app.schemas.preflight import PreFlightRequest

def test_key_generation_and_signing():
    private_pem, public_pem = CryptoService.generate_key_pair()
    payload = {"mandate_id": "m_1", "user_id": "u_1"}
    
    token = CryptoService.sign_mandate(payload, private_pem)
    decoded = CryptoService.verify_signature(token, public_pem)
    
    assert decoded["mandate_id"] == "m_1"
    assert decoded["user_id"] == "u_1"

def test_invalid_signature_blocks_preflight():
    private_pem_1, public_pem_1 = CryptoService.generate_key_pair()
    _, public_pem_2 = CryptoService.generate_key_pair()
    
    payload = {"mandate_id": "m_1", "user_id": "u_1"}
    token = CryptoService.sign_mandate(payload, private_pem_1)

    rules = MandateSchema(
        cumulative_budget=500.00,
        approval_threshold=100.00,
        expiry=datetime.now(timezone.utc) + timedelta(days=1),
        allowed_categories=["electronics"],
        merchant_constraints={"allow": ["Amazon"], "deny": []}
    )
    request = PreFlightRequest(
        mandate_id="m_1",
        amount=Decimal("50.00"),
        category="electronics",
        merchant="Amazon"
    )

    response = PolicyEngine.evaluate(
        mandate_rules=rules,
        request=request,
        is_revoked=False,
        signature=token,
        public_key_pem=public_pem_2
    )

    assert response.decision == PreFlightDecision.BLOCK
    assert "signature verification failed" in response.reason.lower()