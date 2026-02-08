from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import UUID, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from models import Base
from utils import TransactionStatus


class Transaction(Base):
    __tablename__ = "transaction"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    amount = Column(Numeric(18, 4), nullable=False)
    wallet_id = Column(
        UUID(as_uuid=True),
        ForeignKey("wallet.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )

    balance_after = Column(Numeric(18, 4), nullable=False, default=0)

    reference_id = Column(String, nullable=True, unique=True)

    status = Column(String, default=TransactionStatus.PENDING.value)
    type = Column(String, nullable=False)
    related_transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("transaction.id", onupdate="CASCADE"),
        nullable=True,
    )
    description = Column(String, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc)
    )

    wallet = relationship("Wallet", back_populates="transactions")
    related_transaction = relationship("Transaction", remote_side=[id])
