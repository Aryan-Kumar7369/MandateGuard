from decimal import Decimal
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Mandate, Delegation, Order, Event, Dispute
from app.services.audit_service import AuditService
from app.services.crypto import CryptoService
from app.services.event_bus import EventBus
from app.schemas.mandate import MandateSchema
from app.schemas.preflight import PreFlightRequest
from app.services.policy_engine import PolicyEngine

router = APIRouter(prefix="/api/v1/demo", tags=["Demo Orchestrator"])

@router.post("/seed")
async def seed_demo_environment(db: Session = Depends(get_db)):
    db.query(Dispute).delete()
    db.query(Event).delete()
    db.query(Order).delete()
    db.query(Delegation).delete()
    db.query(Mandate).delete()
    db.commit()

    now = datetime.now(timezone.utc)
    priv_key, _ = CryptoService.generate_key_pair()

    root_rules = {
        "cumulative_budget": 500.0,
        "approval_threshold": 100.0,
        "expiry": (now + timedelta(days=30)).isoformat(),
        "allowed_categories": ["software", "electronics", "cloud"],
        "merchant_constraints": {"allow": ["GitHub", "Amazon", "AWS"], "deny": ["UntrustedVendor"]},
        "allowed_shipping_destinations": ["US"]
    }
    root_sig = CryptoService.sign_mandate({"mandate_id": "m_corp_root", "rules": root_rules}, priv_key)

    root_mandate = Mandate(
        id="m_corp_root",
        user_id="executive_buyer@paypal.com",
        rules=root_rules,
        signature=f"FIDO2_PASSKEY.{root_sig[:32]}",
        is_revoked=False
    )
    db.add(root_mandate)
    db.commit()

    AuditService.record_event(
        db=db,
        event_type="MANDATE_CREATED",
        mandate_id="m_corp_root",
        payload={"user_id": "executive_buyer@paypal.com", "budget": 500.0}
    )

    child_rules = {
        "cumulative_budget": 150.0,
        "approval_threshold": 50.0,
        "expiry": (now + timedelta(days=7)).isoformat(),
        "allowed_categories": ["software"],
        "merchant_constraints": {"allow": ["GitHub"], "deny": []},
        "allowed_shipping_destinations": ["US"]
    }
    child_sig = CryptoService.sign_mandate({"mandate_id": "m_corp_devops", "rules": child_rules}, priv_key)

    child_mandate = Mandate(
        id="m_corp_devops",
        user_id="executive_buyer@paypal.com",
        rules=child_rules,
        signature=f"FIDO2_PASSKEY.{child_sig[:32]}",
        is_revoked=False
    )
    db.add(child_mandate)

    delegation = Delegation(
        id="del_root_devops",
        parent_mandate_id="m_corp_root",
        child_mandate_id="m_corp_devops",
        delegated_by="agent_orchestrator",
        delegated_to="agent_devops_specialist"
    )
    db.add(delegation)
    db.commit()

    AuditService.record_event(
        db=db,
        event_type="MANDATE_DELEGATED",
        mandate_id="m_corp_devops",
        payload={"parent": "m_corp_root", "child": "m_corp_devops", "budget": 150.0}
    )

    order1 = Order(
        id="ord_demo_01",
        paypal_order_id="PAYPAL_TX_GITHUB_101",
        mandate_id="m_corp_devops",
        amount=45.0,
        currency="USD",
        status="CAPTURED",
        payload={"merchant": "GitHub", "category": "software"}
    )
    db.add(order1)
    db.commit()

    AuditService.record_event(
        db=db,
        event_type="PAYPAL_CHECKOUT_EXECUTION",
        mandate_id="m_corp_devops",
        payload={"order_id": "ord_demo_01", "amount": 45.0, "merchant": "GitHub", "status": "CAPTURED"}
    )

    dispute1 = Dispute(
        id="DISPUTE_DEMO_01",
        order_id="ord_demo_01",
        mandate_id="m_corp_devops",
        amount=Decimal("45.00"),
        reason="UNAUTHORIZED_AGENT_TRANSACTION",
        status="OPEN"
    )
    db.add(dispute1)
    db.commit()

    AuditService.record_event(
        db=db,
        event_type="DISPUTE_CREATED",
        mandate_id="m_corp_devops",
        payload={"dispute_id": "DISPUTE_DEMO_01", "amount": 45.0, "reason": "UNAUTHORIZED_AGENT_TRANSACTION"}
    )

    await EventBus.publish("MANDATE_CREATED", {"mandate_id": "m_corp_root", "user_id": "executive_buyer@paypal.com"})
    await EventBus.publish("MANDATE_CREATED", {"mandate_id": "m_corp_devops", "user_id": "executive_buyer@paypal.com"})

    return {
        "status": "seeded",
        "root_mandate_id": "m_corp_root",
        "sub_mandate_id": "m_corp_devops",
        "dispute_id": "DISPUTE_DEMO_01"
    }

@router.post("/act1")
async def trigger_act1_happy_path(db: Session = Depends(get_db)):
    mandate = db.query(Mandate).filter(Mandate.id == "m_corp_devops").first()
    if not mandate:
        return {"error": "Seed environment first"}

    rules = MandateSchema(**mandate.rules)
    req = PreFlightRequest(
        mandate_id="m_corp_devops",
        amount=Decimal("35.00"),
        category="software",
        merchant="GitHub",
        shipping_destination="US"
    )
    result = PolicyEngine.evaluate(rules, req, is_revoked=mandate.is_revoked, db=db)

    AuditService.record_event(
        db=db,
        event_type="PRE_FLIGHT_CHECK",
        mandate_id=mandate.id,
        payload={"amount": 35.0, "merchant": "GitHub", "decision": result.decision.value, "reason": result.reason}
    )

    await EventBus.publish("PRE_FLIGHT_EVALUATED", {
        "mandate_id": mandate.id,
        "decision": result.decision.value,
        "amount": 35.0,
        "reason": result.reason
    })

    return {"act": 1, "decision": result.decision.value, "reason": result.reason}

@router.post("/act2")
async def trigger_act2_delegation_attack(db: Session = Depends(get_db)):
    mandate = db.query(Mandate).filter(Mandate.id == "m_corp_devops").first()
    if not mandate:
        return {"error": "Seed environment first"}

    rules = MandateSchema(**mandate.rules)
    req = PreFlightRequest(
        mandate_id="m_corp_devops",
        amount=Decimal("250.00"),
        category="software",
        merchant="GitHub",
        shipping_destination="US"
    )
    result = PolicyEngine.evaluate(rules, req, is_revoked=mandate.is_revoked, db=db)

    AuditService.record_event(
        db=db,
        event_type="PRE_FLIGHT_CHECK",
        mandate_id=mandate.id,
        payload={"amount": 250.0, "merchant": "GitHub", "decision": result.decision.value, "reason": result.reason}
    )

    await EventBus.publish("PRE_FLIGHT_EVALUATED", {
        "mandate_id": mandate.id,
        "decision": result.decision.value,
        "amount": 250.0,
        "reason": result.reason
    })

    return {"act": 2, "decision": result.decision.value, "reason": result.reason}

@router.post("/act3")
async def trigger_act3_killswitch(db: Session = Depends(get_db)):
    mandate = db.query(Mandate).filter(Mandate.id == "m_corp_devops").first()
    if not mandate:
        return {"error": "Seed environment first"}

    mandate.is_revoked = True
    db.commit()

    AuditService.record_event(
        db=db,
        event_type="MANDATE_REVOKED",
        mandate_id=mandate.id,
        payload={"reason": "Emergency kill-switch triggered by human controller"}
    )

    await EventBus.publish("MANDATE_REVOKED", {"mandate_id": mandate.id})

    rules = MandateSchema(**mandate.rules)
    req = PreFlightRequest(
        mandate_id="m_corp_devops",
        amount=Decimal("15.00"),
        category="software",
        merchant="GitHub",
        shipping_destination="US"
    )
    result = PolicyEngine.evaluate(rules, req, is_revoked=True, db=db)

    await EventBus.publish("PRE_FLIGHT_EVALUATED", {
        "mandate_id": mandate.id,
        "decision": result.decision.value,
        "amount": 15.0,
        "reason": result.reason
    })

    return {"act": 3, "mandate_id": mandate.id, "status": "REVOKED", "subsequent_decision": result.decision.value}
