from datetime import datetime, timezone

from sqlalchemy import UUID, Column, DateTime, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import relationship

from models import Base


class Token(Base):
    __tablename__ = "token"
    id = Column(Integer, Sequence("token_id_seq"), primary_key=True)
    token_hash = Column(String, nullable=False)
    user_id = Column(
        UUID,
        ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    user = relationship("User", backref="tokens")
