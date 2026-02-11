from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from utils import Gender, RoleEnum


class User(BaseModel):
    username: str = Field(None, min_length=4, max_length=50)
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    gender: Gender
    email: str
    is_active: Optional[bool] = True


class UserCreate(User):
    role: Optional[Literal[RoleEnum.USER]] = RoleEnum.USER
    password: str = Field(None, min_length=8, max_length=16)
    confirm_password: str = Field(None, min_length=8, max_length=16)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if info.data.get("password") and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=4, max_length=50)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    gender: Optional[Gender] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    old_password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=16,
    )
    new_password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=16,
    )
    confirm_new_password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=16,
    )

    @field_validator("confirm_new_password")
    @classmethod
    def passwords_match(cls, v, info):
        if v and info.data.get("new_password") and v != info.data["new_password"]:
            raise ValueError("New passwords do not match")
        return v


class UserResponse(User):
    id: UUID
    is_verified: Optional[bool] = False
    model_config = ConfigDict(from_attributes=True, extra="allow")

    user_roles: Optional[List[int]] = Field(
        alias="user_role", serialization_alias="user_roles", default_factory=list
    )

    @field_validator("user_roles", mode="before")
    @classmethod
    def extract_roles_ids(cls, v):
        if isinstance(v, list):
            return [user_role.role_id for user_role in v]
        return v


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=8, max_length=16)
    new_password: str = Field(min_length=8, max_length=16)
    confirm_new_password: str = Field(min_length=8, max_length=16)

    @field_validator("confirm_new_password")
    @classmethod
    def passwords_match(cls, v, info):
        if info.data.get("new_password") and v != info.data["new_password"]:
            raise ValueError("New passwords do not match")
        return v


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=50)
    confirm_new_password: str = Field(min_length=8, max_length=50)

    @field_validator("confirm_new_password")
    @classmethod
    def passwords_match(cls, v, info):
        if info.data.get("new_password") and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class EmailChangeRequest(BaseModel):
    new_email: EmailStr
