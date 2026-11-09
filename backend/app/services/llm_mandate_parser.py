import os
import json
import httpx
from datetime import datetime, timedelta, timezone
from app.schemas.mandate import MandateSchema

class LLMMandateParser:
    @staticmethod
    def parse_natural_language_prompt(prompt: str) -> MandateSchema:
        api_key = os.getenv("GROQ_API_KEY")
        base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        
        if not api_key:
            return LLMMandateParser._fallback_parser(prompt)

        system_instruction = (
            "You are a mandate compiler. Extract spend permissions into a JSON object matching this schema:\n"
            "{\n"
            '  "cumulative_budget": float,\n'
            '  "approval_threshold": float,\n'
            '  "expiry": "ISO8601 string",\n'
            '  "allowed_categories": [string],\n'
            '  "merchant_constraints": {"allow": [string], "deny": [string]},\n'
            '  "allowed_shipping_destinations": [string]\n'
            "}"
        )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }

        try:
            with httpx.Client() as client:
                resp = client.post(f"{base_url}/chat/completions", headers=headers, json=body, timeout=10.0)
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return MandateSchema(**parsed)
        except Exception:
            pass

        return LLMMandateParser._fallback_parser(prompt)

    @staticmethod
    def _fallback_parser(prompt: str) -> MandateSchema:
        return MandateSchema(
            cumulative_budget=200.00,
            approval_threshold=50.00,
            expiry=datetime.now(timezone.utc) + timedelta(days=7),
            allowed_categories=["general", "electronics"],
            merchant_constraints={"allow": ["Amazon"], "deny": []},
            allowed_shipping_destinations=[]
        )