import uuid
from sqlalchemy import Column, String, Text, Boolean, BigInteger, DateTime, Enum, Integer, event
from backend.constants.model_constant import UserStatusEnum, RoleStatusEnum, RoleTypeEnum, PermissionTypeEnum, \
    PermissionActionEnum, PermissionStatusEnum
from backend.models.base import IBaseModel


class Role(IBaseModel):
    __tablename__ = "sys_role"
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(RoleStatusEnum), default=RoleStatusEnum.ACTIVE)
    role_type = Column(Enum(RoleTypeEnum), default=RoleTypeEnum.CUSTOM)



class Permission(IBaseModel):
    __tablename__ = "sys_permission"
    code = Column(String(50), unique=True, index=True, nullable=False, comment="基于resource,action生成 user::create")
    name = Column(String(50), nullable=True, comment="")
    resource = Column(String(50), nullable=False, comment="eg: user")
    action = Column(Enum(PermissionActionEnum), default=PermissionActionEnum.CREATE, nullable=False)
    description = Column(Text, nullable=True)
    permission_type = Column(Enum(PermissionTypeEnum), default=PermissionTypeEnum.API)
    level = Column(Integer, default=1)
    status = Column(Enum(PermissionStatusEnum), default=PermissionStatusEnum.ACTIVE)
    api_endpoint = Column(String(255))
    http_method = Column(String(10))

    def __repr__(self):
        return f"<Permission(id={self.id}, code='{self.code}', name='{self.name}')>"


# 添加事件监听器，自动为超级用户分配所有权限
@event.listens_for(Permission, 'after_insert')
async def assign_permission_to_superuser(mapper, connection, target):
    pass



class User(IBaseModel):
    __tablename__ = "sys_user"
    guid = Column(String(36), default=lambda: str(uuid.uuid4()), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    nickname = Column(String(50), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone = Column(String(20), unique=True, nullable=True)
    status = Column(Enum(UserStatusEnum), default=UserStatusEnum.ACTIVE)
    is_superuser = Column(Boolean, default=False)
    last_login_ip = Column(String(50), nullable=True)
    last_login_time = Column(DateTime(timezone=True), nullable=True)
    mfa_enabled = Column(Boolean, default=False)


    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

    def has_permission(self, permissions: list, resource: str, action: str) -> bool:
        if self.is_superuser:
            return True
        for permission in permissions:
            if permission.resource == resource and permission.action == action:
                return True
        return False


class UserRole(IBaseModel):
    __tablename__ = 'sys_user_role'

    user_id = Column(String(36), index=True, nullable=False)
    role_id = Column(BigInteger, index=True, nullable=False, default=5)

    __table_args__ = (
    )


class RolePermission(IBaseModel):
    __tablename__ = 'sys_role_permission'

    role_id = Column(BigInteger, index=True, nullable=False)
    permission_id = Column(BigInteger, index=True, nullable=False)
    __table_args__ = (
    )