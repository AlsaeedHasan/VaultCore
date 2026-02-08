from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import dependencies
import models
import oauth2
import schemas
import utils
from database import get_db

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get(
    "/",
    response_model=List[schemas.UserResponse],
    dependencies=[
        Depends(dependencies.check_permission(utils.PermissionEnum.GET_USERS.value))
    ],
)
def get_users(
    current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
    db: Session = Depends(get_db),
):
    return db.query(models.User).all()


@router.get(
    "/get_user/{username}/",
    response_model=schemas.UserResponse,
    dependencies=[
        Depends(dependencies.check_permission(utils.PermissionEnum.GET_USERS.value))
    ],
)
async def get_user(
    username: str,
    current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"User '{username}' not found")
    return user


@router.get("/me/", response_model=schemas.UserResponse)
async def get_user(
    current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.username == current_user.username)
        .first()
    )
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"User '{current_user.username}' not found"
        )
    return user


@router.put("/me/", response_model=schemas.UserResponse)
async def update_me(
    user: schemas.UserUpdate,
    current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
    db: Session = Depends(get_db),
):
    db_user = (
        db.query(models.User)
        .filter(models.User.username == current_user.username)
        .first()
    )
    if not db_user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    try:
        if user.username and user.username != db_user.username:
            db_user.username = user.username

        if user.first_name and user.first_name != db_user.first_name:
            db_user.first_name = user.first_name

        if user.last_name and user.last_name != db_user.last_name:
            db_user.last_name = user.last_name

        if user.middle_name and user.middle_name != db_user.middle_name:
            db_user.middle_name = user.middle_name

        if user.gender and user.gender != db_user.gender:
            db_user.gender = user.gender

        if user.email and user.email != db_user.email:
            db_user.email = user.email
            db_user.is_verified = False

        db.commit()

        db.refresh(db_user)
        return db_user

    except IntegrityError as e:
        db.rollback()
        if "username" in str(e.orig):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username already taken")
        elif "email" in str(e.orig):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already in use")
        else:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Data constraint violation"
            )
    except Exception:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to update user"
        )


@router.post(
    "/assign-role/",
    response_model=schemas.UserRoleResponse,
    dependencies=[
        Depends(dependencies.check_permission(utils.PermissionEnum.CHANGE_ROLES.value))
    ],
)
async def assign_role(
    user_role: schemas.UserRoleCreate,
    current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_role.user_id).first()

    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"User not found.")

    role_id = user_role.role_id
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found.")

    current_weight = utils.get_user_max_weight(current_user.user_roles, db)

    target_role_ids = [r.role_id for r in user.user_role]
    target_weight = utils.get_user_max_weight(target_role_ids, db)

    if current_weight <= target_weight:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Not enough privileges to modify this user."
        )

    existing_role = (
        db.query(models.UserRole)
        .filter(models.UserRole.user_id == user.id, models.UserRole.role_id == role_id)
        .first()
    )

    if existing_role:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Role is already assigned to the user."
        )

    try:
        new_user_role = models.UserRole(user_id=user.id, role_id=role_id)
        db.add(new_user_role)
        db.commit()
        db.refresh(new_user_role)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Role is already assigned to the user."
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to assign user role."
        )

    return schemas.UserRoleResponse(role_id=role_id)


@router.delete(
    "/revoke-role/",
    dependencies=[
        Depends(dependencies.check_permission(utils.PermissionEnum.CHANGE_ROLES.value))
    ],
)
async def revoke_role(
    user_role: schemas.UserRoleCreate,
    current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_role.user_id).first()

    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"User not found.")

    role_id = user_role.role_id
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found.")

    current_weight = utils.get_user_max_weight(current_user.user_roles, db)

    target_role_ids = [r.role_id for r in user.user_role]
    target_weight = utils.get_user_max_weight(target_role_ids, db)

    if current_weight <= target_weight:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Not enough privileges to modify this user."
        )

    existing_role = (
        db.query(models.UserRole)
        .filter(models.UserRole.user_id == user.id, models.UserRole.role_id == role_id)
        .first()
    )

    if not existing_role:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Role is not assigned to the user."
        )

    try:
        db.delete(existing_role)
        db.commit()
        return {"message": f"Role {role_id} successfully revoked from user {user.id}"}
    except Exception:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to revoke user role."
        )
