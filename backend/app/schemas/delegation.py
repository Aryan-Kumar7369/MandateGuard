from datetime import datetime
from pydantic import BaseModel
from app.schemas.mandate import MandateSchema

class DelegationCreateRequest(BaseModel):
    parent_mandate_id: str
    delegated_by: str
    delegated_to: str
    child_rules: MandateSchema

class DelegationResponse(BaseModel):
    id: str
    parent_mandate_id: str
    child_mandate_id: str
    delegated_by: str
    delegated_to: str
    created_at: datetime