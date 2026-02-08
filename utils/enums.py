from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class RoleEnum(str, Enum):
    SUPERUSER = "superuser"
    ADMIN = "admin"
    STAFF = "staff"
    SUPPORT = "support"
    USER = "user"

    @property
    def weight(self) -> int:
        weights = {
            "superuser": 1000,
            "admin": 800,
            "staff": 500,
            "support": 500,
            "user": 0,
        }
        return weights[self.value]

    def can_manage(self, other_role: "RoleEnum") -> bool:
        return self.weight > other_role.weight


class PermissionEnum(str, Enum):
    ADD_ADMIN = "add_admin"
    REMOVE_ADMIN = "remove_admin"
    ADD_STAFF = "add_staff"
    REMOVE_STAFF = "remove_staff"
    ADD_SUPPORT = "add_support"
    REMOVE_SUPPORT = "remove_support"
    ADD_USER = "add_user"
    REMOVE_USER = "remove_user"
    CHANGE_ROLES = "change_roles"
    CHANGE_PERMISSIONS = "change_permissions"
    GET_USERS = "get_users"


class CurrencyEnum(str, Enum):
    EGP = "EGP"
    USD = "USD"
    EUR = "EUR"
    SAR = "SAR"


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
