from datetime import datetime, timezone
from decimal import Decimal
from app.schemas.mandate import MandateSchema, PreFlightDecision
from app.schemas.preflight import PreFlightRequest, PreFlightResponse

class PolicyEngine:
    @staticmethod
    def evaluate(
        mandate_rules: MandateSchema,
        request: PreFlightRequest,
        is_revoked: bool,
        current_spent: Decimal = Decimal("0.00")
    ) -> PreFlightResponse:
        now = datetime.now(timezone.utc)

        
        if is_revoked:
            return PreFlightResponse(
                decision=PreFlightDecision.BLOCK,
                reason="Mandate has been explicitly revoked via kill-switch.",
                mandate_id=request.mandate_id
            )

        
        expiry = mandate_rules.expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        if now > expiry:
            return PreFlightResponse(
                decision=PreFlightDecision.BLOCK,
                reason=f"Mandate expired at {expiry.isoformat()}.",
                mandate_id=request.mandate_id
            )

        
        merchant = request.merchant.strip().lower()
        merchant_constraints = mandate_rules.merchant_constraints
        deny_list = [m.lower() for m in merchant_constraints.get("deny", [])]
        allow_list = [m.lower() for m in merchant_constraints.get("allow", [])]

        if merchant in deny_list:
            return PreFlightResponse(
                decision=PreFlightDecision.BLOCK,
                reason=f"Merchant '{request.merchant}' is explicitly blocked.",
                mandate_id=request.mandate_id
            )

        if allow_list and merchant not in allow_list:
            return PreFlightResponse(
                decision=PreFlightDecision.BLOCK,
                reason=f"Merchant '{request.merchant}' is not in the allowed merchants list.",
                mandate_id=request.mandate_id
            )

        
        category = request.category.strip().lower()
        allowed_categories = [c.lower() for c in mandate_rules.allowed_categories]
        if category not in allowed_categories:
            return PreFlightResponse(
                decision=PreFlightDecision.BLOCK,
                reason=f"Category '{request.category}' is not authorized by this mandate.",
                mandate_id=request.mandate_id
            )

        
        projected_total = current_spent + request.amount
        budget = Decimal(str(mandate_rules.cumulative_budget))
        if projected_total > budget:
            return PreFlightResponse(
                decision=PreFlightDecision.BLOCK,
                reason=f"Transaction amount ({request.amount}) + previous spend ({current_spent}) exceeds cumulative budget of {budget}.",
                mandate_id=request.mandate_id
            )

        
        threshold = Decimal(str(mandate_rules.approval_threshold))
        if request.amount > threshold:
            return PreFlightResponse(
                decision=PreFlightDecision.ASK_HUMAN,
                reason=f"Transaction amount ({request.amount}) exceeds single-purchase threshold of {threshold}. Human verification required.",
                mandate_id=request.mandate_id
            )

        
        return PreFlightResponse(
            decision=PreFlightDecision.ALLOW,
            reason="Pre-flight check passed successfully.",
            mandate_id=request.mandate_id
        )