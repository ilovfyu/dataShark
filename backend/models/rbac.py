import asyncio
import uuid
from sqlalchemy import Column, String, Text, Boolean, BigInteger, DateTime, Enum, Integer, event, UniqueConstraint
from backend.constants.model_constant import UserStatusEnum, RoleStatusEnum, RoleTypeEnum, PermissionTypeEnum, \
    PermissionActionEnum, PermissionStatusEnum, HttpMethodEnum, PermissionResourceEnum
from backend.core.framework.mysql import db
from backend.models.base import IBaseModel
class Role(IBaseModel):
    __tablename__ = "sys_role"
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(RoleStatusEnum), default=RoleStatusEnum.ACTIVE)
    role_type = Column(Enum(RoleTypeEnum), default=RoleTypeEnum.SYSTEM)
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"



class Permission(IBaseModel):
    __tablename__ = "sys_permission"
    code = Column(String(50), unique=True, index=True, nullable=False, comment="基于resource,action生成 user::create")
    name = Column(String(50), nullable=True, comment="")
    resource = Column(Enum(PermissionResourceEnum), default=PermissionResourceEnum.COMMON, nullable=False)
    action = Column(Enum(PermissionActionEnum), default=PermissionActionEnum.CREATE, nullable=False)
    description = Column(Text, nullable=True)
    permission_type = Column(Enum(PermissionTypeEnum), default=PermissionTypeEnum.API)
    level = Column(Integer, default=1)
    status = Column(Enum(PermissionStatusEnum), default=PermissionStatusEnum.ACTIVE)
    api_endpoint = Column(String(255))
    http_method = Column(Enum(HttpMethodEnum))

    def __repr__(self):
        return f"<Permission(id={self.id}, code='{self.code}', name='{self.name}')>"


# 添加事件监听器，自动为超级用户分配所有权限
@event.listens_for(Permission, 'after_insert')
def assign_permission_to_superuser(mapper, connection, target):
    """
    当创建新权限时，自动为所有超级用户分配该权限
    :param mapper: SQLAlchemy映射器
    :param connection: 数据库连接
    :param target: 新创建的权限对象
    """
    # 使用数据库连接直接执行SQL，避免异步问题
    try:
        # 直接使用同步方式处理权限分配
        _assign_permission_to_superuser_sync(target)
    except Exception as e:
        from backend.core.logs.loguru_config import Logger
        logger = Logger.get_logger()
        logger.error(f"为超级用户分配权限时出错: {str(e)}")


def _assign_permission_to_superuser_sync(target):
    """同步方式分配权限给超级用户的实现"""
    try:
        from backend.models.rbac import Role, RolePermission
        from sqlalchemy import text

        # 获取同步数据库连接
        sync_engine = db.engine.sync_engine if hasattr(db.engine, 'sync_engine') else db.engine

        with sync_engine.connect() as conn:
            # 查找管理员角色（ID为1的系统管理员角色）
            admin_role_result = conn.execute(
                text("SELECT id FROM sys_role WHERE id = 1")
            ).first()


            # 如果找到了管理员角色，则为管理员角色分配新权限
            if admin_role_result:
                admin_role_id = admin_role_result[0]

                # 检查是否已经为管理员角色分配了该权限
                existing_result = conn.execute(
                    text(
                        "SELECT 1 FROM sys_role_permission WHERE role_id = :role_id AND permission_id = :permission_id"),
                    {"role_id": admin_role_id, "permission_id": target.id}
                ).first()

                # 如果还没有分配，则添加权限到管理员角色
                if not existing_result:
                    conn.execute(
                        text(
                            "INSERT INTO sys_role_permission (role_id, permission_id) VALUES (:role_id, :permission_id)"),
                        {"role_id": admin_role_id, "permission_id": target.id}
                    )
                    conn.commit()

    except Exception as e:
        # 记录错误但不中断权限创建过程
        from backend.core.logs.loguru_config import Logger
        logger = Logger.get_logger()
        logger.error(f"为超级用户分配权限时出错: {str(e)}")
        # 不重新抛出异常，以免影响权限创建流程



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



class PermissionGroup(IBaseModel):
    """
    权限组模型
    """
    __tablename__ = "sys_permission_group"

    name = Column(String(100), unique=True, index=True, nullable=False, comment="权限组名称")
    code = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()),  nullable=False, comment="权限组编码")
    description = Column(Text, nullable=True, comment="权限组描述")
    status = Column(Enum(PermissionStatusEnum), default=PermissionStatusEnum.ACTIVE, comment="状态")
    sort_order = Column(Integer, default=0, comment="排序")

    def __repr__(self):
        return f"<PermissionGroup(id={self.id}, name='{self.name}', code='{self.code}')>"





class GroupPermissions(IBaseModel):
    """
    权限组与权限关联模型
    """
    __tablename__ = "sys_group_permission"

    group_code = Column(String(36), index=True, nullable=False, comment="权限组code")
    permission_id = Column(BigInteger, index=True, nullable=False, comment="权限ID")

    __table_args__ = (
        UniqueConstraint('group_code', 'permission_id', name='uq_group_permission'),
    )
    def __repr__(self):
        return f"<GroupPermission(group_id={self.group_id}, permission_id={self.permission_id})>"





class RolePermissionGroup(IBaseModel):
    """
    角色与权限组关联模型
    """
    __tablename__ = 'sys_role_permission_group'

    role_id = Column(BigInteger, index=True, nullable=False)
    group_code = Column(BigInteger, index=True, nullable=False)

    __table_args__ = (
        UniqueConstraint('role_id', 'group_code', name='uq_role_permission_group'),
    )
    def __repr__(self):
        return f"<RolePermissionGroup(role_id={self.role_id}, group_code={self.group_code})>"

