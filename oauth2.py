from datetime import datetime, timedelta, timezone
from os import getenv
from typing import Dict, Literal, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from utils import get_expire_minutes, verify_password

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/auth/token", refreshUrl="api/v1/auth/refresh"
)

SECRET_KEY = getenv("SECRET_KEY", "auth_app_secret_key")
ALGORITHM = getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE = int(getenv("ACCESS_TOKEN_EXPIRE", 30))  # in minutes
REFRESH_TOKEN_EXPIRE = int(getenv("REFRESH_TOKEN_EXPIRE", 7200))  # in minutes


def authenticate_user(
    username: str, password: str, db: Session
) -> schemas.UserResponse:
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"User {username} NOT found")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect password")
    return schemas.UserResponse.model_validate(user)


def create_token(
    data: Dict,
    expires_delta: Optional[timedelta] = None,
    token_type: Literal[
        "access", "refresh", "verification", "password_reset"
    ] = "access",
) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=get_expire_minutes(token_type)
        )

    to_encode.update({"exp": expire, "type": token_type})
    return jwt.encode(to_encode, SECRET_KEY, ALGORITHM)


def verify_token(
    token: str,
    db: Session,
    expected_type: Literal[
        "access", "refresh", "verification", "password_reset"
    ] = "access",
) -> schemas.UserResponse:
    credentials_exception = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        if db.query(models.RevokedToken.token).filter_by(token=token).first():
            raise credentials_exception

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        token_version: int = payload.get("v")

        if username is None or token_type != expected_type:
            raise credentials_exception

        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = (
        db.query(models.User)
        .filter(models.User.username == token_data.username)
        .first()
    )
    if user is None or token_version != user.token_version:
        raise credentials_exception
    return schemas.UserResponse.model_validate(user)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> schemas.UserResponse:
    user = verify_token(token, db, expected_type="access")
    return schemas.UserResponse.model_validate(user)


async def get_current_active_user(
    current_user: schemas.UserResponse = Depends(get_current_user),
) -> schemas.UserResponse:
    if not current_user.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Inactive User")
    return current_user
