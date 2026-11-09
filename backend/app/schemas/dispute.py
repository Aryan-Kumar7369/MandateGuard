from pydantic import BaseModel

class DisputeSummary(BaseModel):
    dispute_id: str
    status: str
    reason: str
    amount: float
    currency: str
    paypal_order_id: str | None = None

class DisputeSyncResponse(BaseModel):
    synced_count: int
    disputes: list[DisputeSummary]