from backend.core.db.mysql import db
from backend.models.rbac import (
    User,
    UserRole,
    Role,
    RolePermission,
    Permission,
)

MODELS = [
    User,
    UserRole,
    Role,
    RolePermission,
    Permission,
]


for model in MODELS:
    db.register_model(model)
