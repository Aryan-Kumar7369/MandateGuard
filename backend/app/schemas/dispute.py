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

class EvidenceBundleResponse(BaseModel):
    dispute_id: str
    order_id: str | None
    paypal_order_id: str | None
    mandate_id: str
    amount: float
    reason: str
    status: str
    mandate_rules: dict | None
    mandate_signature: str | None
    delegation_chain: list[dict]
    audit_trail: list[dict]
    chain_integrity_valid: bool
    assembled_at: str

class RecourseChecklistItem(BaseModel):
    rule: str
    satisfied: bool
    details: str

class RecoursePreviewResponse(BaseModel):
    dispute_id: str
    policy_reference: str
    readiness_percentage: float
    checklist: list[RecourseChecklistItem]
    advisory_explanation: str
