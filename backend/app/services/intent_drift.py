import os
import json
import httpx
from pydantic import BaseModel
from app.schemas.mandate import PreFlightDecision

class DriftAnalysisResult(BaseModel):
    drift_detected: bool
    confidence_score: float
    reasoning: str
    suggested_action: PreFlightDecision

class IntentDriftDetector:
    @staticmethod
    def analyze_drift(original_prompt: str, cart_description: str, item_amount: float) -> DriftAnalysisResult:
        api_key = os.getenv("GROQ_API_KEY")
        base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
        model = os.getenv("GROQ_DRIFT_MODEL", "llama-3.1-8b-instant")

        if not api_key:
            return DriftAnalysisResult(
                drift_detected=False,
                confidence_score=0.0,
                reasoning="Groq API key unconfigured; failing safe to deterministic rules.",
                suggested_action=PreFlightDecision.ALLOW
            )

        system_prompt = (
            "You are an intent-drift safety monitor for AI agent shopping.\n"
            "Compare the user's original request with the cart item details.\n"
            "Detect subtle drift, unexpected warranties, address changes, or product swaps.\n"
            "Respond in JSON:\n"
            '{"drift_detected": bool, "confidence_score": float, "reasoning": string, "suggested_action": "ALLOW" | "ASK_HUMAN"}\n'
            "CRITICAL: Drift can ONLY escalate to ASK_HUMAN. It must NEVER override a BLOCK."
        )

        user_content = f"Original Request: {original_prompt}\nCart Item: {cart_description}\nAmount: ${item_amount}"

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "response_format": {"type": "json_object"}
        }

        try:
            with httpx.Client() as client:
                endpoint = f"{base_url}/chat/completions"
                res = client.post(endpoint, headers=headers, json=body, timeout=5.0)
                if res.status_code == 200:
                    data = json.loads(res.json()["choices"][0]["message"]["content"])
                    action = PreFlightDecision.ASK_HUMAN if data.get("drift_detected") else PreFlightDecision.ALLOW
                    return DriftAnalysisResult(
                        drift_detected=data.get("drift_detected", False),
                        confidence_score=float(data.get("confidence_score", 0.0)),
                        reasoning=data.get("reasoning", "No drift detected."),
                        suggested_action=action
                    )
        except Exception as e:
            return DriftAnalysisResult(
                drift_detected=True,
                confidence_score=1.0,
                reasoning=f"LLM drift check timeout or error: {str(e)}",
                suggested_action=PreFlightDecision.ASK_HUMAN
            )

        return DriftAnalysisResult(
            drift_detected=False,
            confidence_score=0.0,
            reasoning="Fallback evaluation.",
            suggested_action=PreFlightDecision.ALLOW
        )