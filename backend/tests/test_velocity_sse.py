import pytest
from datetime import datetime, timezone
from app.models import Mandate, Event
from app.services.event_bus import EventBus

def create_active_mandate(db, mandate_id: str) -> Mandate:
    mandate = Mandate(
        id=mandate_id,
        user_id="user_velocity_test",
        rules={
            "cumulative_budget": 1000.0,
            "approval_threshold": 200.0,
            "expiry": datetime.now(timezone.utc).isoformat(),
            "allowed_categories": ["electronics"],
            "merchant_constraints": {"allow": ["Amazon"], "deny": []},
            "allowed_shipping_destinations": []
        },
        signature=None,
        is_revoked=False
    )
    db.add(mandate)
    db.commit()
    return mandate

def test_velocity_limit_pauses_agent(db, client):
    create_active_mandate(db, "mandate_vel_1")

    for i in range(5):
        event = Event(
            id=f"evt_vel_{i}",
            event_type="PRE_FLIGHT_CHECK",
            mandate_id="mandate_vel_1",
            payload={"amount": 10.0, "decision": "ALLOW"},
            previous_hash="000",
            current_hash=f"hash_{i}"
        )
        db.add(event)
    db.commit()

    response = client.post(
        "/api/v1/preflight",
        json={
            "mandate_id": "mandate_vel_1",
            "amount": 10.0,
            "category": "electronics",
            "merchant": "Amazon"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "ASK_HUMAN"
    assert "SECURITY PAUSE: Velocity threshold exceeded" in data["reason"]

@pytest.mark.anyio
async def test_sse_event_bus_publishing_and_generator():
    queue = EventBus.subscribe()
    
    await EventBus.publish("TEST_EVENT", {"status": "success", "mandate_id": "m_test_123"})
    
    gen = EventBus.event_generator(queue)
    
    connected_frame = await gen.__anext__()
    assert connected_frame == ": connected\n\n"
    
    event_frame = await gen.__anext__()
    assert "event: TEST_EVENT" in event_frame
    assert "m_test_123" in event_frame
    
    EventBus.unsubscribe(queue)