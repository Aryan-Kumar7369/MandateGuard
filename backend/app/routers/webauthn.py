import base64
import os
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/webauthn", tags=["WebAuthn"])

class ChallengeResponse(BaseModel):
    challenge: str
    rp_id: str
    user_id: str

class VerifyAssertionRequest(BaseModel):
    credential_id: str
    client_data_json: str
    authenticator_data: str
    signature: str

@router.get("/challenge", response_model=ChallengeResponse)
def get_webauthn_challenge(user_id: str = "user_demo"):
    random_bytes = os.urandom(32)
    challenge_b64 = base64.urlsafe_b64encode(random_bytes).decode("utf-8").rstrip("=")
    return ChallengeResponse(
        challenge=challenge_b64,
        rp_id="localhost",
        user_id=user_id
    )

@router.post("/verify-assertion")
def verify_webauthn_assertion(payload: VerifyAssertionRequest):
    if not payload.signature or not payload.credential_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid WebAuthn assertion payload."
        )
    return {
        "verified": True,
        "credential_id": payload.credential_id,
        "auth_method": "FIDO2_WEBAUTHN_PASSKEY"
    }