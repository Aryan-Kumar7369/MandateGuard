from sqlalchemy import String, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase
from sqlalchemy.sql import func
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Mandate(Base):
    __tablename__ = "mandates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36))
    rules: Mapped[dict] = mapped_column(JSON)
    signature: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Delegation(Base):
    __tablename__ = "delegations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    parent_mandate_id: Mapped[str] = mapped_column(String(36), ForeignKey("mandates.id"))
    child_mandate_id: Mapped[str] = mapped_column(String(36), ForeignKey("mandates.id"))
    delegated_by: Mapped[str] = mapped_column(String(36))
    delegated_to: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    mandate_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("mandates.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
    previous_hash: Mapped[str] = mapped_column(String(64))
    current_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paypal_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mandate_id: Mapped[str] = mapped_column(String(36), ForeignKey("mandates.id"))
    amount: Mapped[float] = mapped_column(Float)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())