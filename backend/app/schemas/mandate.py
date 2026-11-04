from enum import Enum
from pydantic import BaseModel
from typing import List
from datetime import datetime
from decimal import Decimal


class PreFlightDecision(Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    ASK_HUMAN = "ASK_HUMAN"



class MandateSchema(BaseModel):
    cumulative_budget: Decimal
    approval_threshold: Decimal
    expiry: datetime
    allowed_categories: List[str]
    merchant_constraints: dict[str, List[str]]