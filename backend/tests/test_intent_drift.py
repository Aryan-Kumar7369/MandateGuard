from unittest.mock import patch
from app.services.intent_drift import IntentDriftDetector
from app.schemas.mandate import PreFlightDecision

@patch("httpx.Client.post")
def test_intent_drift_detected(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"drift_detected": true, "confidence_score": 0.9, "reasoning": "Extended warranty added to cart", "suggested_action": "ASK_HUMAN"}'
                }
            }
        ]
    }
    res = IntentDriftDetector.analyze_drift("Buy running shoes", "Running shoes + 2 Year Extended Warranty", 120.0)
    assert res.drift_detected is True
    assert res.suggested_action == PreFlightDecision.ASK_HUMAN

def test_intent_drift_fallback_without_api_key():
    res = IntentDriftDetector.analyze_drift("Buy running shoes", "Running shoes", 50.0)
    assert res.drift_detected is False or res.suggested_action in [PreFlightDecision.ALLOW, PreFlightDecision.ASK_HUMAN]