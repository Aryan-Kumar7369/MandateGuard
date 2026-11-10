import time
import httpx

BASE_URL = "http://localhost:8000/api/v1"

def trigger_live_dashboard_events():
    print("Connecting to live FastAPI Uvicorn server at http://localhost:8000...")
    
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Create a new mandate
        print("\n[1/4] Registering a new Mandate via API...")
        mandate_payload = {
            "user_id": "user_demo_123",
            "rules": {
                "cumulative_budget": 500.0,
                "approval_threshold": 100.0,
                "expiry": "2027-12-31T23:59:59Z",
                "allowed_categories": ["electronics", "software"],
                "merchant_constraints": {"allow": ["Amazon", "GitHub"], "deny": []},
                "allowed_shipping_destinations": ["US"]
            }
        }
        res = client.post("/mandates/", json=mandate_payload)
        if res.status_code != 201:
            print(f"Error creating mandate: {res.text}")
            return

        mandate_data = res.json()
        mandate_id = mandate_data["id"]
        print(f"--> Created Mandate ID: {mandate_id}")
        time.sleep(1.5)

        # 2. Trigger Pre-Flight Check (ALLOW)
        print("\n[2/4] Sending Pre-Flight Check ($45.00 for GitHub)...")
        pf_allow = {
            "mandate_id": mandate_id,
            "amount": 45.00,
            "category": "software",
            "merchant": "GitHub",
            "shipping_destination": "US"
        }
        res = client.post("/preflight", json=pf_allow)
        print(f"--> Response: {res.json()['decision']} | Reason: {res.json()['reason']}")
        time.sleep(1.5)

        # 3. Trigger Pre-Flight Check (ASK_HUMAN threshold trigger)
        print("\n[3/4] Sending High-Value Pre-Flight Check ($250.00 for Amazon)...")
        pf_threshold = {
            "mandate_id": mandate_id,
            "amount": 250.00,
            "category": "electronics",
            "merchant": "Amazon",
            "shipping_destination": "US"
        }
        res = client.post("/preflight", json=pf_threshold)
        print(f"--> Response: {res.json()['decision']} | Reason: {res.json()['reason']}")
        time.sleep(1.5)

        # 4. Trigger Emergency Revocation (Kill-Switch)
        print("\n[4/4] Triggering Emergency Kill-Switch API...")
        res = client.post(f"/mandates/{mandate_id}/revoke")
        print(f"--> Mandate {mandate_id} status: REVOKED")

    print("\n=======================================================")
    print(" LIVE DEMO COMPLETE")
    print("=======================================================")

if __name__ == "__main__":
    trigger_live_dashboard_events()