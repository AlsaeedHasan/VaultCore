from pydantic import BaseModel, ConfigDict

from utils import RoleEnum


class RoleResponse(BaseModel):
    id: int
    role: RoleEnum
    model_config = ConfigDict(from_attributes=True)
