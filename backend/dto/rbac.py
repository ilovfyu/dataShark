from typing import Optional, List
from backend.dto.base import BaseSchema
from datetime import datetime

# Permission DTOs
class PermissionBase(BaseSchema):
    name: str
    description: Optional[str] = None
    resource: str
    action: str

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None

class PermissionResponse(PermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

# Role DTOs
class RoleBase(BaseSchema):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = None

class RoleUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[int]] = None

class RoleResponse(RoleBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

# UserRole DTOs
class UserRoleCreate(BaseSchema):
    user_id: int
    role_id: int

class UserRoleResponse(UserRoleCreate):
    id: int
    created_at: datetime
    updated_at: datetime

# RolePermission DTOs
class RolePermissionCreate(BaseSchema):
    role_id: int
    permission_id: int

class RolePermissionResponse(RolePermissionCreate):
    id: int
    created_at: datetime
    updated_at: datetime
