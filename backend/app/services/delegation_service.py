from datetime import timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import Mandate, Delegation
from app.schemas.mandate import MandateSchema

class DelegationService:
    @staticmethod
    def validate_sub_mandate(parent: MandateSchema, child: MandateSchema) -> tuple[bool, str]:
        if Decimal(str(child.cumulative_budget)) > Decimal(str(parent.cumulative_budget)):
            return False, f"Child budget ({child.cumulative_budget}) exceeds parent budget ({parent.cumulative_budget})."

        if Decimal(str(child.approval_threshold)) > Decimal(str(parent.approval_threshold)):
            return False, f"Child approval threshold ({child.approval_threshold}) exceeds parent threshold ({parent.approval_threshold})."

        p_expiry = parent.expiry if parent.expiry.tzinfo else parent.expiry.replace(tzinfo=timezone.utc)
        c_expiry = child.expiry if child.expiry.tzinfo else child.expiry.replace(tzinfo=timezone.utc)
        if c_expiry > p_expiry:
            return False, f"Child expiry ({c_expiry.isoformat()}) extends beyond parent expiry ({p_expiry.isoformat()})."

        p_cats = set(c.lower() for c in parent.allowed_categories)
        c_cats = set(c.lower() for c in child.allowed_categories)
        if not c_cats.issubset(p_cats):
            invalid_cats = c_cats - p_cats
            return False, f"Child contains unauthorized categories: {invalid_cats}."

        p_deny = set(m.lower() for m in parent.merchant_constraints.get("deny", []))
        c_allow = set(m.lower() for m in child.merchant_constraints.get("allow", []))
        if p_deny.intersection(c_allow):
            return False, "Child allows merchants explicitly denied by parent."

        p_allow = set(m.lower() for m in parent.merchant_constraints.get("allow", []))
        if p_allow and not c_allow.issubset(p_allow):
            return False, "Child allow list includes merchants not allowed by parent."

        return True, "Delegation authorization narrowing validated successfully."

    @classmethod
    def validate_full_chain(cls, db: Session, target_mandate_id: str) -> tuple[bool, str, str | None]:
        current_id = target_mandate_id
        visited = set()

        while True:
            if current_id in visited:
                return False, f"Cyclic delegation loop detected at mandate '{current_id}'.", current_id
            visited.add(current_id)

            mandate = db.query(Mandate).filter(Mandate.id == current_id).first()
            if not mandate:
                return False, f"Broken link: Mandate '{current_id}' does not exist.", current_id

            if mandate.is_revoked:
                return False, f"Broken link: Mandate '{current_id}' is revoked.", current_id

            delegation = db.query(Delegation).filter(Delegation.child_mandate_id == current_id).first()
            if not delegation:
                break

            parent_mandate = db.query(Mandate).filter(Mandate.id == delegation.parent_mandate_id).first()
            if not parent_mandate:
                return False, f"Broken link: Parent mandate '{delegation.parent_mandate_id}' missing.", delegation.parent_mandate_id

            parent_rules = MandateSchema(**parent_mandate.rules)
            child_rules = MandateSchema(**mandate.rules)
            is_valid, reason = cls.validate_sub_mandate(parent_rules, child_rules)

            if not is_valid:
                return False, f"Broken link between parent '{parent_mandate.id}' and child '{mandate.id}': {reason}", mandate.id

            current_id = parent_mandate.id

        return True, "Full delegation chain verified successfully.", None