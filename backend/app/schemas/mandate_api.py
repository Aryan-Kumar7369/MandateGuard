from pydantic import BaseModel
from app.schemas.mandate import MandateSchema

class MandateCreateRequest(BaseModel):
    user_id: str
    rules: MandateSchema

class MandateSignRequest(BaseModel):
    mandate_id: str
    private_key_pem: str

class MandateResponse(BaseModel):
    id: str
    user_id: str
    rules: dict
    signature: str | None
    is_revoked: bool