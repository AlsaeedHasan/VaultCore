import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    VARCHAR,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship

from models import Base


class User(Base):
    __tablename__ = "user"
    __table_args__ = (CheckConstraint("gender IN ('male', 'female')"),)
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    username = Column(VARCHAR(50), nullable=False, unique=True)
    first_name = Column(VARCHAR(50), nullable=False)
    last_name = Column(VARCHAR(50), nullable=False)
    middle_name = Column(VARCHAR(50))
    email = Column(VARCHAR(150), nullable=False, unique=True)
    gender = Column(VARCHAR(7), nullable=False)
    password_hash = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    token_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now)

    user_role = relationship("UserRole", back_populates="user", lazy="joined")
    wallets = relationship(
        "Wallet", back_populates="user", cascade="all, delete-orphan"
    )
