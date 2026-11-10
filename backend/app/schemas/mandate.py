from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field

class PreFlightDecision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    ASK_HUMAN = "ASK_HUMAN"

class MandateSchema(BaseModel):
    cumulative_budget: Decimal = Field(..., gt=0)
    approval_threshold: Decimal = Field(..., gt=0)
    expiry: datetime
    allowed_categories: list[str]
    merchant_constraints: dict[str, list[str]]
    allowed_shipping_destinations: list[str] = Field(default_factory=list)

class MandateCreateRequest(BaseModel):
    user_id: str
    rules: MandateSchema

class MandateResponse(BaseModel):
    id: str
    user_id: str
    rules: MandateSchema
    signature: str | None = None
    is_revoked: bool
    created_at: datetime