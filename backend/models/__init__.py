from backend.core.db.mysql import db
from backend.models.rbac import (
    User,
    UserRole,
    Role,
    RolePermission,
    Permission,
    PermissionGroup,
    GroupPermissions
)
from backend.models.workspace import (
    Workspace,
    UserWorkspace
)

MODELS = [
    User,
    UserRole,
    Role,
    RolePermission,
    Permission,
    Workspace,
    UserWorkspace,
    GroupPermissions,
    PermissionGroup
]


for model in MODELS:
    db.register_model(model)
