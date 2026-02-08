from sqlalchemy import VARCHAR, Column, Integer, Sequence
from sqlalchemy.orm import relationship

from models import Base


class Permission(Base):
    __tablename__ = "permission"
    id = Column(Integer, Sequence("permission_id_seq"), primary_key=True)
    permission = Column(VARCHAR(50), nullable=False, unique=True)
    role_permission = relationship("RolePermission", back_populates="permission")
