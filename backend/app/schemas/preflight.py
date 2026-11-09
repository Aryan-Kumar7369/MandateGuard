from datetime import datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, Field
from app.schemas.mandate import PreFlightDecision

class PreFlightRequest(BaseModel):
    mandate_id: str
    amount: Decimal = Field(..., gt=0)
    category: str
    merchant: str

class PreFlightResponse(BaseModel):
    decision: PreFlightDecision
    reason: str
    mandate_id: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))