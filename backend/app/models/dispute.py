from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime
from app.models.model import Base

class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, nullable=True)
    mandate_id = Column(String, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, default="OPEN", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))