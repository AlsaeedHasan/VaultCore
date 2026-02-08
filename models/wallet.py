from uuid import uuid4

from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from models import Base


class Wallet(Base):
    __tablename__ = "wallet"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    currency = Column(String(3), nullable=False)
    balance = Column(Numeric(18, 4), default=0.0000, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="wallets")
    transactions = relationship("Transaction", back_populates="wallet")

    __table_args__ = (
        UniqueConstraint("user_id", "currency", name="unique_user_currency_wallet"),
    )
