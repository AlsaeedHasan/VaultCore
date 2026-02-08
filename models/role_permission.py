from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from models import Base


class RolePermission(Base):
    __tablename__ = "role_permission"
    role_id = Column(
        Integer,
        ForeignKey("role.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    permission_id = Column(
        Integer,
        ForeignKey("permission.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    role = relationship("Role", back_populates="role_permission")
    permission = relationship("Permission", back_populates="role_permission")
