from sqlalchemy import Column, Integer, Sequence, String
from sqlalchemy.orm import relationship

from models import Base


class Role(Base):
    __tablename__ = "role"
    id = Column(Integer, Sequence("role_id_seq"), primary_key=True)
    role = Column(String, nullable=False, unique=True)
    user_role = relationship("UserRole", back_populates="role")
    role_permission = relationship("RolePermission", back_populates="role")
