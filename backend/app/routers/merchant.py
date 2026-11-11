import hashlib
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Mandate, Order
from app.schemas.mandate import MandateSchema

router = APIRouter(prefix="/api/v1/merchant", tags=["Merchant Signal"])


class MerchantVerificationResponse(BaseModel):
    mandate_id: str
    status: str
    within_limits: bool
    verification_token: str


class MerchantVerifyRequest(BaseModel):
    mandate_id: str
    amount: float
    merchant: str
    category: str


class MerchantVerifySignalResponse(BaseModel):
    is_valid: bool
    badge_status: str
    remaining_budget: float
    mandate_id: str
    merchant: str
    verification_token: str
    message: str


@router.get("/verify-signal/{mandate_id}", response_model=MerchantVerificationResponse)
def verify_merchant_signal(mandate_id: str, db: Session = Depends(get_db)):
    mandate = db.query(Mandate).filter(Mandate.id == mandate_id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found.")

    is_valid = not mandate.is_revoked
    raw_token = f"{mandate.id}:{mandate.is_revoked}:{mandate.user_id}"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    return MerchantVerificationResponse(
        mandate_id=mandate.id,
        status="VALID" if is_valid else "REVOKED",
        within_limits=is_valid,
        verification_token=f"v_sig_{token_hash[:16]}"
    )


@router.post("/verify-signal", response_model=MerchantVerifySignalResponse)
def verify_mandate_signal_post(
    request: MerchantVerifyRequest,
    db: Session = Depends(get_db)
):
    mandate = db.query(Mandate).filter(Mandate.id == request.mandate_id).first()
    if not mandate:
        return MerchantVerifySignalResponse(
            is_valid=False,
            badge_status="MANDATE_NOT_FOUND",
            remaining_budget=0.0,
            mandate_id=request.mandate_id,
            merchant=request.merchant,
            verification_token="v_sig_invalid",
            message=f"Mandate '{request.mandate_id}' does not exist."
        )

    raw_token = f"{mandate.id}:{mandate.is_revoked}:{mandate.user_id}"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    v_token = f"v_sig_{token_hash[:16]}"

    if mandate.is_revoked:
        return MerchantVerifySignalResponse(
            is_valid=False,
            badge_status="MANDATE_REVOKED",
            remaining_budget=0.0,
            mandate_id=request.mandate_id,
            merchant=request.merchant,
            verification_token=v_token,
            message="Mandate has been revoked by user kill-switch."
        )

    rules = MandateSchema(**mandate.rules)

    spent_result = (
        db.query(func.coalesce(func.sum(Order.amount), 0.0))
        .filter(Order.mandate_id == request.mandate_id, Order.status == "CAPTURED")
        .scalar()
    )
    spent = Decimal(str(spent_result))
    remaining = float(rules.cumulative_budget - spent)

    req_amount = Decimal(str(request.amount))
    if (spent + req_amount) > rules.cumulative_budget:
        return MerchantVerifySignalResponse(
            is_valid=False,
            badge_status="BUDGET_EXCEEDED",
            remaining_budget=max(0.0, remaining),
            mandate_id=request.mandate_id,
            merchant=request.merchant,
            verification_token=v_token,
            message=f"Requested amount (${request.amount}) exceeds remaining budget (${remaining:.2f})."
        )

    allow_list = rules.merchant_constraints.get("allow", [])
    deny_list = rules.merchant_constraints.get("deny", [])

    if deny_list and request.merchant in deny_list:
        return MerchantVerifySignalResponse(
            is_valid=False,
            badge_status="MERCHANT_DENIED",
            remaining_budget=max(0.0, remaining),
            mandate_id=request.mandate_id,
            merchant=request.merchant,
            verification_token=v_token,
            message=f"Merchant '{request.merchant}' is explicitly denied by mandate rules."
        )

    if allow_list and request.merchant not in allow_list:
        return MerchantVerifySignalResponse(
            is_valid=False,
            badge_status="MERCHANT_NOT_ALLOWED",
            remaining_budget=max(0.0, remaining),
            mandate_id=request.mandate_id,
            merchant=request.merchant,
            verification_token=v_token,
            message=f"Merchant '{request.merchant}' is not in allowed merchants list."
        )

    if rules.allowed_categories and request.category not in rules.allowed_categories:
        return MerchantVerifySignalResponse(
            is_valid=False,
            badge_status="CATEGORY_DISALLOWED",
            remaining_budget=max(0.0, remaining),
            mandate_id=request.mandate_id,
            merchant=request.merchant,
            verification_token=v_token,
            message=f"Category '{request.category}' is not allowed for this mandate."
        )

    return MerchantVerifySignalResponse(
        is_valid=True,
        badge_status="VERIFIED_MANDATE",
        remaining_budget=remaining,
        mandate_id=request.mandate_id,
        merchant=request.merchant,
        verification_token=v_token,
        message="Valid mandate within authorized limits. Merchant authorization signal confirmed."
    )