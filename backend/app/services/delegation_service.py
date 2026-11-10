from sqlalchemy.orm import Session
from app.models import Mandate, Delegation
from app.schemas.mandate import MandateSchema

class DelegationService:
    @classmethod
    def validate_sub_mandate(cls, parent: MandateSchema, child: MandateSchema) -> tuple[bool, str]:
        if child.cumulative_budget > parent.cumulative_budget:
            return False, f"Child budget ({child.cumulative_budget}) exceeds parent budget ({parent.cumulative_budget})."

        if child.approval_threshold > parent.approval_threshold:
            return False, f"Child threshold ({child.approval_threshold}) exceeds parent threshold ({parent.approval_threshold})."

        if child.expiry > parent.expiry:
            return False, "Child expiry extends beyond parent expiry."

        if not set(child.allowed_categories).issubset(set(parent.allowed_categories)):
            return False, "Child allowed categories are not a subset of parent allowed categories."

        if parent.allowed_shipping_destinations:
            if not child.allowed_shipping_destinations:
                return False, "Child shipping destinations cannot be unrestricted when parent has destination restrictions."
            if not set(child.allowed_shipping_destinations).issubset(set(parent.allowed_shipping_destinations)):
                return False, "Child shipping destinations are not a subset of parent shipping destinations."

        parent_denied = set(parent.merchant_constraints.get("deny", []))
        child_allowed = set(child.merchant_constraints.get("allow", []))
        if parent_denied.intersection(child_allowed):
            return False, "Child allows merchant explicitly denied by parent."

        return True, "Sub-mandate satisfies narrowing invariants."

    @classmethod
    def validate_full_chain(cls, db: Session, target_mandate_id: str) -> tuple[bool, str, str | None]:
        curr_id = target_mandate_id
        visited = set()

        while curr_id:
            if curr_id in visited:
                return False, f"Cycle detected in delegation chain at mandate '{curr_id}'.", curr_id
            visited.add(curr_id)

            mandate = db.query(Mandate).filter(Mandate.id == curr_id).first()
            if not mandate:
                return False, f"Mandate '{curr_id}' not found.", curr_id

            if mandate.is_revoked:
                return False, f"Mandate '{curr_id}' in chain is revoked.", curr_id

            delegation = db.query(Delegation).filter(Delegation.child_mandate_id == curr_id).first()
            if not delegation:
                break

            curr_id = delegation.parent_mandate_id

        return True, "Delegation chain is valid and unrevoked.", None