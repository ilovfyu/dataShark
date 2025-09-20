from backend.core.framework.mysql import db
from backend.models.rbac import (
    User,
    UserRole,
    Role,
    RolePermission,
    Permission,
    PermissionGroup,
    GroupPermissions,
    RolePermissionGroup
)
from backend.models.workspace import (
    Workspace,
    UserWorkspace
)

MODELS = [
    User, UserRole, Role, RolePermission,
    Permission, Workspace, UserWorkspace,
    GroupPermissions,
    PermissionGroup,
    RolePermissionGroup
]


for model in MODELS:
    db.register_model(model)
