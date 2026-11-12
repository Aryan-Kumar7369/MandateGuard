from decimal import Decimal
from pydantic import BaseModel
from app.schemas.mandate import PreFlightDecision

class CheckoutExecutionRequest(BaseModel):
    mandate_id: str
    paypal_order_id: str
    category: str
    merchant: str

class CheckoutExecutionResponse(BaseModel):
    order_id: str
    paypal_order_id: str
    decision: PreFlightDecision
    status: str
    amount: Decimal
    currency: str
    reason: str

class CreateOrderRequest(BaseModel):
    amount: float
    currency: str = "USD"
    description: str = "Software Subscription - GitHub Team"

class CreateOrderResponse(BaseModel):
    paypal_order_id: str
    status: str
    approval_url: str | None = None
