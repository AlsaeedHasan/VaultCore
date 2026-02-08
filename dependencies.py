from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import oauth2
import schemas
from database import get_db


def check_permission(
    permission: str,
) -> Callable:

    def permission_dependency(
        current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
        db: Session = Depends(get_db),
    ) -> bool:
        user_role_ids = current_user.user_roles
        has_permission = bool(
            db.query(models.RolePermission)
            .join(models.Permission)
            .filter(
                models.RolePermission.role_id.in_(user_role_ids),
                models.Permission.permission == permission,
            )
            .all()
        )

        if not has_permission:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=f"You do not have the permission: {permission}",
            )

        return True

    return permission_dependency
