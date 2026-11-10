import sys
import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.core.database import SessionLocal, engine
from app.models import Base, Mandate, Delegation, Order, Event
from app.schemas.mandate import MandateSchema
from app.schemas.preflight import PreFlightRequest
from app.services.policy_engine import PolicyEngine
from app.services.delegation_service import DelegationService
from app.services.audit_service import AuditService
from app.services.llm_mandate_parser import LLMMandateParser
from app.services.intent_drift import IntentDriftDetector
from app.services.event_bus import EventBus
from app.services.velocity_service import VelocityService


def run_pipeline_check():
    print("==========================================")
    print(" STARTING MANDATEGUARD PIPELINE CHECK")
    print("==========================================")

    # 1. Database Re-initialization
    print("\n--- 1. DATABASE RE-INITIALIZATION ---")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    print("[PASS] Database schema recreated successfully.")

    # 2. Natural Language LLM Mandate Parsing
    print("\n--- 2. GROQ LLM PARSER TEST ---")
    prompt = "Allow my agent to spend up to $400 on electronics from Amazon until next month"
    parsed_rules = LLMMandateParser.parse_natural_language_prompt(prompt)
    assert parsed_rules.cumulative_budget > 0
    print(f"[PASS] LLM extracted budget: ${parsed_rules.cumulative_budget}")
    print(f"[PASS] LLM extracted categories: {parsed_rules.allowed_categories}")

    # 3. Mandate Storage & Audit Logging
    print("\n--- 3. MANDATE CREATION & AUDIT LOGGING ---")
    root_mandate = Mandate(
        id="m_e2e_root",
        user_id="user_e2e",
        rules=parsed_rules.model_dump(mode="json"),
        signature=None,
        is_revoked=False
    )
    db.add(root_mandate)
    db.commit()
    AuditService.record_event(
        db=db,
        event_type="MANDATE_CREATED",
        mandate_id="m_e2e_root",
        payload={"user_id": "user_e2e", "budget": float(parsed_rules.cumulative_budget)}
    )
    print("[PASS] Root mandate persisted & audit event logged.")

    # 4. Multi-hop Delegation & Sub-mandate Narrowing
    print("\n--- 4. MULTI-HOP DELEGATION CHAIN NARROWING ---")
    now = datetime.now(timezone.utc)
    child_rules = MandateSchema(
        cumulative_budget=Decimal("150.00"),
        approval_threshold=Decimal("50.00"),
        expiry=now + timedelta(days=2),
        allowed_categories=["electronics"],
        merchant_constraints={"allow": ["Amazon"], "deny": []},
        allowed_shipping_destinations=["US"]
    )
    
    is_valid, narrowing_reason = DelegationService.validate_sub_mandate(parsed_rules, child_rules)
    assert is_valid is True, f"Sub-mandate validation failed: {narrowing_reason}"

    child_mandate = Mandate(
        id="m_e2e_child",
        user_id="user_e2e",
        rules=child_rules.model_dump(mode="json"),
        signature=None,
        is_revoked=False
    )
    db.add(child_mandate)
    db.flush()  # Flush child mandate first to respect PostgreSQL foreign key constraints

    delegation = Delegation(
        id="del_e2e_1",
        parent_mandate_id="m_e2e_root",
        child_mandate_id="m_e2e_child",
        delegated_by="agent_root",
        delegated_to="agent_sub"
    )
    db.add(delegation)
    db.commit()

    chain_valid, chain_msg, broken_link = DelegationService.validate_full_chain(db, "m_e2e_child")
    assert chain_valid is True, f"Chain check failed: {chain_msg}"
    print(f"[PASS] Multi-hop chain verified (root -> child). Status: {chain_msg}")

    # 5. Policy Engine Pre-flight Decision
    print("\n--- 5. PRE-FLIGHT POLICY EVALUATION ---")
    pf_request = PreFlightRequest(
        mandate_id="m_e2e_child",
        amount=Decimal("30.00"),
        category="electronics",
        merchant="Amazon",
        shipping_destination="US"
    )
    pf_result = PolicyEngine.evaluate(
        mandate_rules=child_rules,
        request=pf_request,
        is_revoked=False,
        db=db
    )
    assert pf_result.decision.value == "ALLOW"
    print(f"[PASS] Policy engine decision: {pf_result.decision.value} ({pf_result.reason})")

    # 6. Groq LLM Intent-Drift Detector
    print("\n--- 6. INTENT-DRIFT ANALYSIS ---")
    drift_result = IntentDriftDetector.analyze_drift(
        original_prompt=prompt,
        cart_description="Sony Wireless Headphones from Amazon",
        item_amount=30.0
    )
    print(f"[PASS] Intent drift check completed.")
    print(f"       - Drift Detected: {drift_result.drift_detected}")
    print(f"       - Suggested Action: {drift_result.suggested_action.value}")
    print(f"       - Reasoning: {drift_result.reasoning}")

    # 7. Velocity Limit Verification
    print("\n--- 7. VELOCITY LIMIT CHECK ---")
    vel_exceeded, vel_reason = VelocityService.check_velocity(db, "m_e2e_child")
    print(f"[PASS] Velocity status: Exceeded={vel_exceeded} ({vel_reason})")

    # 8. Event Bus SSE Publishing
    print("\n--- 8. REAL-TIME EVENT BUS PUBLISHING ---")
    asyncio.run(EventBus.publish("PRE_FLIGHT_EVALUATED", {
        "mandate_id": "m_e2e_child",
        "decision": pf_result.decision.value,
        "amount": 30.0,
        "reason": pf_result.reason
    }))
    print("[PASS] Broadcasted event to active SSE stream subscribers.")

    # 9. Audit Log Cryptographic Hash-Chain Verification
    print("\n--- 9. AUDIT CHAIN INTEGRITY CHECK ---")
    is_chain_valid, verify_msg, event_count = AuditService.verify_chain(db)
    assert is_chain_valid is True, f"Audit chain broken: {verify_msg}"
    print(f"[PASS] Audit log integrity verified across {event_count} block events.")

    db.close()
    print("\n==========================================")
    print(" ALL PIPELINE CHECKS PASSED SUCCESSFULLY!")
    print("==========================================")


if __name__ == "__main__":
    run_pipeline_check()