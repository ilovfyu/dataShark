from functools import wraps
from typing import Callable, List, Optional, Union
from fastapi import HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.rbac import Permission, Role, RolePermission, UserRole
from backend.core.db.mysql import get_db
from backend.core.logs.loguru_config import Logger

logger = Logger.get_logger()

def require_permission(
    resource: str,
    action: str,
    check_superuser: bool = True
):
    """
    权限检查装饰器
    :param resource: 资源名称 (如: user, role, permission)
    :param action: 操作名称 (如: create, read, update, delete)
    :param check_superuser: 是否检查超级用户权限
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取request对象
            request = _get_request_from_args(args, kwargs)
            if request is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无法获取请求对象"
                )

            # 检查用户是否已认证
            current_user = getattr(request.state, 'current_user', None)
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证的用户",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 超级用户检查
            if check_superuser and current_user.is_superuser:
                return await func(*args, **kwargs)

            # 检查用户权限
            has_perm = await _check_user_permission(current_user.guid, resource, action, request)
            if not has_perm:
                logger.warning(
                    f"Permission denied: User {current_user.username} "
                    f"attempted to access {resource}:{action}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少 {resource}:{action} 权限"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_permissions(
    permissions: List[tuple],  # [(resource, action), ...]
    require_all: bool = True,  # True: 需要所有权限, False: 满足任一权限即可
    check_superuser: bool = True
):
    """
    多权限检查装饰器
    :param permissions: 权限列表 [(resource, action), ...]
    :param require_all: 是否需要所有权限
    :param check_superuser: 是否检查超级用户权限
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取request对象
            request = _get_request_from_args(args, kwargs)
            if request is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无法获取请求对象"
                )

            # 检查用户是否已认证
            current_user = getattr(request.state, 'current_user', None)
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证的用户",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 超级用户检查
            if check_superuser and current_user.is_superuser:
                return await func(*args, **kwargs)

            # 检查用户权限
            satisfied_count = 0
            for resource, action in permissions:
                has_perm = await _check_user_permission(current_user.guid, resource, action, request)
                if has_perm:
                    satisfied_count += 1
                    if not require_all:  # 满足任一权限即可
                        break

            if require_all and satisfied_count != len(permissions):
                logger.warning(
                    f"Permission denied: User {current_user.username} "
                    f"lacks required permissions: {permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少必要的权限"
                )

            if not require_all and satisfied_count == 0:
                logger.warning(
                    f"Permission denied: User {current_user.username} "
                    f"lacks any of the permissions: {permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少任一所需权限"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_permission_by_code(permission_code: str, check_superuser: bool = True):
    """
    通过权限代码检查权限装饰器
    :param permission_code: 权限代码 (如: user:create, role:read)
    :param check_superuser: 是否检查超级用户权限
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取request对象
            request = _get_request_from_args(args, kwargs)
            if request is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无法获取请求对象"
                )

            # 检查用户是否已认证
            current_user = getattr(request.state, 'current_user', None)
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证的用户",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 超级用户检查
            if check_superuser and current_user.is_superuser:
                return await func(*args, **kwargs)

            # 检查用户权限
            has_perm = await _check_user_permission_by_code(current_user.guid, permission_code, request)
            if not has_perm:
                logger.warning(
                    f"Permission denied: User {current_user.username} "
                    f"attempted to access {permission_code}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少 {permission_code} 权限"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role_name: Union[str, List[str]], check_superuser: bool = True):
    """
    角色检查装饰器
    :param role_name: 角色名称或角色名称列表
    :param check_superuser: 是否检查超级用户权限
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取request对象
            request = _get_request_from_args(args, kwargs)
            if request is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无法获取请求对象"
                )

            # 检查用户是否已认证
            current_user = getattr(request.state, 'current_user', None)
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证的用户",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 超级用户检查
            if check_superuser and current_user.is_superuser:
                return await func(*args, **kwargs)

            # 检查用户角色
            has_role = await _check_user_role(current_user.guid, role_name, request)
            if not has_role:
                logger.warning(
                    f"Role denied: User {current_user.username} "
                    f"does not have role {role_name}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少 {role_name} 角色"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 辅助函数
def _get_request_from_args(args, kwargs) -> Optional[Request]:
    """从参数中获取Request对象"""
    # 从位置参数中查找
    for arg in args:
        if isinstance(arg, Request):
            return arg

    # 从关键字参数中查找
    for value in kwargs.values():
        if isinstance(value, Request):
            return value

    return None

async def _check_user_permission(user_id: str, resource: str, action: str, request) -> bool:
    """
    检查用户是否具有指定资源和操作的权限
    :param user_id: 用户ID
    :param resource: 资源名称
    :param action: 操作名称
    :param request: 请求对象
    :return: 是否具有权限
    """
    try:
        # 获取数据库会话
        db_gen = get_db()
        db: AsyncSession = await db_gen.__anext__()

        try:
            # 查询用户的角色
            user_role_stmt = select(UserRole.role_id).where(UserRole.user_id == user_id)
            user_role_result = await db.execute(user_role_stmt)
            role_ids = [row[0] for row in user_role_result.all()]

            if not role_ids:
                return False

            # 查询角色对应的权限ID
            role_perm_stmt = select(RolePermission.permission_id).where(
                RolePermission.role_id.in_(role_ids)
            )
            role_perm_result = await db.execute(role_perm_stmt)
            permission_ids = [row[0] for row in role_perm_result.all()]

            if not permission_ids:
                return False

            # 查询具体权限
            perm_stmt = select(Permission).where(
                Permission.id.in_(permission_ids),
                Permission.resource == resource,
                Permission.action == action,
                Permission.status == "active"
            )
            perm_result = await db.execute(perm_stmt)
            permission = perm_result.scalar_one_or_none()

            return permission is not None
        finally:
            await db.close()
    except Exception as e:
        logger.error(f"Error checking user permission: {e}")
        return False

async def _check_user_permission_by_code(user_id: str, permission_code: str, request) -> bool:
    """
    通过权限代码检查用户权限
    :param user_id: 用户ID
    :param permission_code: 权限代码
    :param request: 请求对象
    :return: 是否具有权限
    """
    try:
        # 获取数据库会话
        db_gen = get_db()
        db: AsyncSession = await db_gen.__anext__()

        try:
            # 查询用户的角色
            user_role_stmt = select(UserRole.role_id).where(UserRole.user_id == user_id)
            user_role_result = await db.execute(user_role_stmt)
            role_ids = [row[0] for row in user_role_result.all()]

            if not role_ids:
                return False

            # 查询角色对应的权限ID
            role_perm_stmt = select(RolePermission.permission_id).where(
                RolePermission.role_id.in_(role_ids)
            )
            role_perm_result = await db.execute(role_perm_stmt)
            permission_ids = [row[0] for row in role_perm_result.all()]

            if not permission_ids:
                return False

            # 查询具体权限
            perm_stmt = select(Permission).where(
                Permission.id.in_(permission_ids),
                Permission.code == permission_code,
                Permission.status == "active"
            )
            perm_result = await db.execute(perm_stmt)
            permission = perm_result.scalar_one_or_none()

            return permission is not None
        finally:
            await db.close()
    except Exception as e:
        logger.error(f"Error checking user permission by code: {e}")
        return False

async def _check_user_role(user_id: str, role_name: Union[str, List[str]], request) -> bool:
    """
    检查用户是否具有指定角色
    :param user_id: 用户ID
    :param role_name: 角色名称或角色名称列表
    :param request: 请求对象
    :return: 是否具有角色
    """
    try:
        # 获取数据库会话
        db_gen = get_db()
        db: AsyncSession = await db_gen.__anext__()

        try:
            # 查询用户的角色
            user_role_stmt = select(UserRole.role_id).where(UserRole.user_id == user_id)
            user_role_result = await db.execute(user_role_stmt)
            role_ids = [row[0] for row in user_role_result.all()]

            if not role_ids:
                return False

            # 构造角色名称查询条件
            if isinstance(role_name, str):
                role_names = [role_name]
            else:
                role_names = role_name

            # 查询角色
            role_stmt = select(Role).where(
                Role.id.in_(role_ids),
                Role.name.in_(role_names),
                Role.status == "active"
            )
            role_result = await db.execute(role_stmt)
            role = role_result.scalar_one_or_none()

            return role is not None
        finally:
            await db.close()
    except Exception as e:
        logger.error(f"Error checking user role: {e}")
        return False
