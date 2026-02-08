import hashlib
import hmac
from os import getenv
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN_EXPIRE = int(getenv("ACCESS_TOKEN_EXPIRE", 30))  # in minutes
REFRESH_TOKEN_EXPIRE = int(getenv("REFRESH_TOKEN_EXPIRE", 7200))  # in minutes
SECRECT_KEY = getenv("SECRET_KEY", "auth_app_secret_key")


def get_expire_minutes(
    token_type: Literal[
        "access", "refresh", "verification", "password_reset"
    ] = "access",
):
    match token_type:
        case "access":
            return ACCESS_TOKEN_EXPIRE
        case "refresh":
            return REFRESH_TOKEN_EXPIRE
        case "verification" | "password_reset":
            return 15


def hash_token(token: str) -> str:
    return hmac.new(
        SECRECT_KEY.encode("utf-8"), token.encode("utf-8"), hashlib.sha256
    ).hexdigest()
