from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: Optional[str] = "Bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
