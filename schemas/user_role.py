from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserRole(BaseModel):
    role_id: int


class UserRoleCreate(UserRole):
    user_id: UUID


class UserRoleResponse(UserRole):
    model_config = ConfigDict(from_attributes=True)
