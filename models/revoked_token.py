from sqlalchemy import Column, String

from models import Base


class RevokedToken(Base):
    __tablename__ = "revoked_token"
    token = Column(String, nullable=False, primary_key=True)
