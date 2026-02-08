import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Cookie,
    Depends,
    HTTPException,
    Header,
    Request,
    Response,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import oauth2
import schemas
import utils
from database import get_db

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Auth"],
)


@router.post("/register/", response_model=schemas.UserResponse)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    user_creation_error_message = "Username already exists"

    password = user.password
    role = user.role
    user_data = user.model_dump(exclude={"password", "confirm_password", "role"})

    password_hash = utils.hash_password(password)

    user_data["password_hash"] = password_hash
    new_db_user = models.User(**user_data)

    db.add(new_db_user)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, user_creation_error_message)

    if role:
        user_role = models.UserRole(
            user_id=new_db_user.id,
            role_id=db.query(models.Role).filter(models.Role.role == role).first().id,
        )
        db.add(user_role)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, user_creation_error_message)

    db.refresh(new_db_user)
    return new_db_user


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = oauth2.authenticate_user(form_data.username, form_data.password, db)
    token_version = db.query(models.User.token_version).filter_by(id=user.id).first()[0]
    data = {"sub": user.username, "v": token_version}

    access_token = oauth2.create_token(data)
    refresh_token = oauth2.create_token(data, token_type="refresh")

    response.set_cookie(
        "refresh_token", refresh_token, httponly=True, secure=False, samesite="lax"
    )

    return schemas.Token(access_token=access_token)


@router.get("/refresh", response_model=schemas.Token)
async def refresh_access_token(
    response: Response,
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing refresh token")

    user = oauth2.verify_token(refresh_token, db, "refresh")
    token_version = db.query(models.User.token_version).filter_by(id=user.id).first()[0]
    data = {"sub": user.username, "v": token_version}

    access_token = oauth2.create_token(data)
    new_refresh_token = oauth2.create_token(data, token_type="refresh")

    try:
        db.add(models.RevokedToken(token=refresh_token))

        response.set_cookie(
            "refresh_token",
            new_refresh_token,
            samesite="lax",
            httponly=True,
            secure=False,
        )

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Token refresh failed"
        )

    return schemas.Token(access_token=access_token)


@router.post("/logout", response_class=Response)
async def logout(
    response: Response,
    current_user: schemas.UserResponse = Depends(oauth2.get_current_user),
    access_token: str = Header(None),
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db),
):

    if refresh_token:
        db.add(models.RevokedToken(token=access_token))
        db.add(models.RevokedToken(token=refresh_token))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Couldn't log out tokens")

    response.set_cookie(
        "refresh_token",
        "",
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=0,
    )

    return Response(status_code=status.HTTP_200_OK)


@router.put("/change-password", response_model=schemas.Token)
async def change_password(
    response: Response,
    username: str,
    data: schemas.ChangePasswordRequest,
    current_user: schemas.UserResponse = Depends(oauth2.get_current_user),
    access_token: str = Header(None),
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db),
):

    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing refresh token.")

    new_password = data.new_password
    hashed_password = utils.hash_password(new_password)

    try:
        user_record = db.query(models.User).filter_by(username=username).first()
        user_record.password_hash = hashed_password
        user_record.token_version += 1
        db.add(models.RevokedToken(token=access_token))
        db.add(models.RevokedToken(token=refresh_token))

        token_data = {"sub": username, "v": user_record.token_version}
        new_access_token = oauth2.create_token(token_data)
        new_refresh_token = oauth2.create_token(token_data, token_type="refresh")

        response.set_cookie(
            "refresh_token",
            new_refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
        )

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Password change failed due to database constraint.",
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An unexpected error occurred while changing password.",
        )

    return schemas.Token(access_token=new_access_token)


@router.post("/verify-email/")
async def verify_email(
    request: Request,
    current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.is_verified:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already verified.")

    token_version = (
        db.query(models.User.token_version).filter_by(id=current_user.id).first()[0]
    )

    expires_delta = timedelta(minutes=utils.get_expire_minutes("verification"))
    expires_at = datetime.now(timezone.utc) + expires_delta

    verify_token = oauth2.create_token(
        {"sub": current_user.username, "v": token_version},
        expires_delta=expires_delta,
        token_type="verification",
    )

    token_hash = utils.hash_token(verify_token)

    verification_url = request.url.replace_query_params(token=verify_token)

    try:
        db_token = models.Token(
            user_id=current_user.id, token_hash=token_hash, expires_at=expires_at
        )
        db.add(db_token)

        with open("mail_templates/verification_mail.html", "r") as template:
            asyncio.create_task(
                utils.send_email(
                    "Email Verification",
                    recipients=[current_user.email],
                    body=template.read().replace(
                        "{verification_url}", verification_url._url
                    ),
                )
            )

        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Couldn't send verification mail."
        )

    return {"msg": "We sent a link to your email, use it to veify your email."}


@router.get("/verify-email/")
async def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
    db_token = (
        db.query(models.Token)
        .filter(models.Token.token_hash == utils.hash_token(token))
        .first()
    )

    if not db_token:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "URL not found.")

    if datetime.now(timezone.utc) > db_token.expires_at:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "URL expired.")

    user = oauth2.verify_token(token, db, "verification")

    db_user = db.query(models.User).filter(models.User.id == user.id).first()
    db_user.is_verified = True

    db.delete(db_token)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Couldn't verify your account."
        )

    return {"msg": "Email Verified."}


# --- 1. Forgot Password Flow ---


@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    data: schemas.PasswordResetRequest,
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user:
        return {"msg": "If the email exists, a reset link has been sent."}

    expires_delta = timedelta(minutes=utils.get_expire_minutes("password_reset"))
    reset_token = oauth2.create_token(
        data={"sub": user.username, "v": user.token_version, "type": "password_reset"},
        expires_delta=expires_delta,
        token_type="password_reset",
    )

    token_hash = utils.hash_token(reset_token)
    expires_at = datetime.now(timezone.utc) + expires_delta

    try:
        db_token = models.Token(
            user_id=user.id, token_hash=token_hash, expires_at=expires_at
        )
        db.add(db_token)
        reset_url = (
            str(request.url_for("reset_password_confirm")).split("?")[0]
            + f"?token={reset_token}"
        )

        # NOTE: Make sure you have a 'password_reset_mail.html' template
        # Or reuse verification template for now
        with open("mail_templates/verification_mail.html", "r") as template:
            asyncio.create_task(
                utils.send_email(
                    "Password Reset Request",
                    recipients=[user.email],
                    body=template.read().replace("{verification_url}", reset_url),
                )
            )
        db.commit()
    except Exception as e:
        db.rollback()
        # Log error in production
        pass

    return {"msg": "If the email exists, a reset link has been sent."}


@router.post("/reset-password-confirm", name="reset_password_confirm")
async def reset_password_confirm(
    data: schemas.PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    try:
        user_response = oauth2.verify_token(data.token, db, "password_reset")
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired token")

    token_hash = utils.hash_token(data.token)
    db_token = (
        db.query(models.Token).filter(models.Token.token_hash == token_hash).first()
    )
    if not db_token:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Token already used or invalid"
        )

    user = db.query(models.User).filter(models.User.id == user_response.id).first()
    user.password_hash = utils.hash_password(data.new_password)
    user.token_version += 1

    db.delete(db_token)
    db.commit()

    return {"msg": "Password updated successfully."}


@router.post("/request-email-change")
async def request_email_change(
    request: Request,
    data: schemas.EmailChangeRequest,
    current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
    db: Session = Depends(get_db),
):
    # 1. Verify Password first (Optional but Recommended for High Security)

    if db.query(models.User).filter(models.User.email == data.new_email).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already in use.")

    expires_delta = timedelta(minutes=15)
    verification_token = oauth2.create_token(
        data={
            "sub": current_user.username,
            "v": db.query(models.User.token_version).filter_by(id=current_user.id).first()[0],
            "new_email": data.new_email,
        },
        expires_delta=expires_delta,
        token_type="verification",
    )

    token_hash = utils.hash_token(verification_token)
    expires_at = datetime.now(timezone.utc) + expires_delta

    try:
        db.add(
            models.Token(
                user_id=current_user.id, token_hash=token_hash, expires_at=expires_at
            )
        )

        verify_url = (
            str(request.url_for("confirm_email_change")).split("?")[0]
            + f"?token={verification_token}"
        )

        with open("mail_templates/verification_mail.html", "r") as template:
            asyncio.create_task(
                utils.send_email(
                    "Confirm Email Change",
                    recipients=[data.new_email],
                    body=template.read().replace("{verification_url}", verify_url),
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to send email."
        )

    return {"msg": "Confirmation link sent to your NEW email."}


@router.get("/confirm-email-change", name="confirm_email_change")
async def confirm_email_change(
    token: str,
    db: Session = Depends(get_db),
):
    try:
        payload = oauth2.jwt.decode(
            token, oauth2.SECRET_KEY, algorithms=[oauth2.ALGORITHM]
        )
        new_email = payload.get("new_email")
        if not new_email:
            raise Exception("Invalid token payload")

        user_response = oauth2.verify_token(token, db, "verification")
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired token")

    token_hash = utils.hash_token(token)
    db_token = (
        db.query(models.Token).filter(models.Token.token_hash == token_hash).first()
    )
    if not db_token:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Token invalid")

    user = db.query(models.User).filter(models.User.id == user_response.id).first()
    user.email = new_email
    user.is_verified = True
    user.token_version += 1

    db.delete(db_token)
    db.commit()

    return {"msg": "Email changed successfully."}
