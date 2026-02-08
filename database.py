from contextlib import asynccontextmanager
from os import getenv
from typing import Iterator

from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

import models
import utils
from models import *
from utils import PermissionEnum, RoleEnum, hash_password

load_dotenv()

DATABASE_USERNAME = getenv("DATABASE_USERNAME", "saeed")
DATABASE_PASSWORD = getenv("DATABASE_PASSWORD", "")
DATABASE_SERVER_IP = getenv("DATABASE_SERVER_IP", "localhost")
DATABASE_PORT = getenv("DATABASE_PORT", 5432)
DATABASE_NAME = getenv("DATABASE_NAME", "fastapi_users")

DATABASE_URI = (
    f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}"
    f"@{DATABASE_SERVER_IP}:{DATABASE_PORT}"
    f"/{DATABASE_NAME}"
)

engine = create_engine(DATABASE_URI)
SessionLocal = sessionmaker(bind=engine)

# Base.metadata.create_all(engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def database_setup(app: FastAPI):
    setup_roles()
    setup_permissions()
    setup_role_permissions()
    setup_superuser()
    yield


def setup_roles():
    with SessionLocal() as db:
        for role in RoleEnum:
            db.add(models.Role(role=role))
            try:
                db.commit()
            except IntegrityError:
                db.rollback()


def setup_permissions():
    with SessionLocal() as db:
        for permission in PermissionEnum:
            db.add(models.Permission(permission=permission))
            try:
                db.commit()
            except IntegrityError:
                db.rollback()


def setup_role_permissions():
    with SessionLocal() as db:
        (
            superuser_role_id,
            admin_role_id,
            staff_role_id,
            _,
            _,
        ) = [
            db.query(models.Role.id).filter(models.Role.role == role).first()[0]
            for role in RoleEnum
        ]

        (
            add_admin_permission_id,
            remove_admin_permission_id,
            add_staff_permission_id,
            remove_staff_permission_id,
            add_support_permission_id,
            remove_support_permission_id,
            add_user_permission_id,
            remove_user_permission_id,
            change_roles_permission_id,
            change_permissions_permission_id,
            get_users_permission_id,
        ) = [
            (
                db.query(models.Permission.id)
                .filter(models.Permission.permission == permission)
                .first()[0]
            )
            for permission in PermissionEnum
        ]

        superuser_permissions = [
            add_admin_permission_id,
            remove_admin_permission_id,
            add_staff_permission_id,
            remove_staff_permission_id,
            add_support_permission_id,
            remove_support_permission_id,
            add_user_permission_id,
            remove_user_permission_id,
            change_roles_permission_id,
            change_permissions_permission_id,
            get_users_permission_id,
        ]

        admin_permissions = [
            add_staff_permission_id,
            remove_staff_permission_id,
            add_support_permission_id,
            add_user_permission_id,
            remove_user_permission_id,
            remove_support_permission_id,
            change_roles_permission_id,
            get_users_permission_id,
        ]

        staff_permissions = [
            add_support_permission_id,
            remove_support_permission_id,
            get_users_permission_id,
        ]

        for role_permissions in [
            (superuser_role_id, superuser_permissions),
            (admin_role_id, admin_permissions),
            (staff_role_id, staff_permissions),
        ]:
            role_id, permissions = role_permissions
            for permission_id in permissions:
                db.add(
                    models.RolePermission(
                        role_id=role_id,
                        permission_id=permission_id,
                    )
                )
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()


def setup_superuser():
    with SessionLocal() as db:

        superuser_username = getenv("SUPERUSER_USERNAME")
        db.add(
            models.User(
                username=superuser_username,
                first_name=getenv("SUPERUSER_FIRST_NAME"),
                last_name=getenv("SUPERUSER_LAST_NAME"),
                middle_name=getenv("SUPERUSER_MIDDLE_NAME"),
                gender=utils.Gender.MALE.value,
                email=getenv("SUPERUSER_EMAIL"),
                password_hash=hash_password(getenv("SUPERUSER_PASSWORD")),
            )
        )

        try:
            db.commit()
        except IntegrityError:
            db.rollback()

        superuser_user_id = (
            db.query(models.User.id)
            .filter(models.User.username == superuser_username)
            .first()
        )

        if superuser_user_id:
            superuser_role = models.UserRole(
                user_id=superuser_user_id[0],
                role_id=db.query(models.Role.id)
                .filter(models.Role.role == utils.RoleEnum.SUPERUSER.value)
                .first()[0],
            )
            db.add(superuser_role)

            try:
                db.commit()
            except IntegrityError:
                db.rollback()
