from sqlalchemy import UUID, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from models import Base


class UserRole(Base):
    __tablename__ = "user_role"
    user_id = Column(
        UUID,
        ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    role_id = Column(
        Integer,
        ForeignKey("role.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    user = relationship("User", back_populates="user_role")
    role = relationship("Role", back_populates="user_role")
