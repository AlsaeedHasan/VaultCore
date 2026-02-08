from typing import List

from sqlalchemy.orm import Session

import models
import utils


def get_user_max_weight(user_role_ids: List[int], db: Session) -> int:
    if not user_role_ids:
        return 0

    roles = db.query(models.Role.role).filter(models.Role.id.in_(user_role_ids)).all()
    weights = [utils.RoleEnum(role[0]).weight for role in roles]
    return max(weights) if weights else 0
