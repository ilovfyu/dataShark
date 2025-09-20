from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.common.errors import ErrorCode
from backend.core.framework.mysql import get_db
from backend.models.rbac import User, Role, Permission, UserRole, RolePermission
from backend.utils.jwt_utils import decode_access_token
from backend.core.logs.loguru_config import Logger

logger = Logger.get_logger()
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前登录用户（强制认证）
    :param credentials: HTTP认证凭证
    :param db: 数据库会话
    :return: 用户对象
    """
    credentials_exception = HTTPException(
        status_code=ErrorCode.UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    try:
        stmt = select(User).where(User.guid == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception

        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户已被禁用"
            )
        return user
    except Exception as e:
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户
    :param current_user: 当前用户
    :return: 当前活跃用户
    """
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前超级用户
    :param current_user: 当前用户
    :return: 当前超级用户
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级用户权限"
        )
    return current_user

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    获取可选的当前用户（如果令牌无效或不存在则返回None）
    :param credentials: HTTP认证凭证（可选）
    :param db: 数据库会话
    :return: 用户对象或None
    """
    if not credentials:
        return None

    try:
        # 解码JWT令牌
        payload = decode_access_token(credentials.credentials)
        if payload is None:
            return None

        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        # 查询用户
        stmt = select(User).where(User.guid == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        # 检查用户状态
        if user and user.status != "active":
            return None

        return user
    except Exception as e:
        logger.error(f"获取可选用户失败: {e}")
        return None

async def require_permission(
    resource: str,
    action: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    权限检查依赖项
    :param resource: 资源名称
    :param action: 操作名称
    :param current_user: 当前用户
    :param db: 数据库会话
    :return: 如果有权限则返回True，否则抛出异常
    """
    # 超级用户检查
    if current_user.is_superuser:
        return True

    try:
        # 查询用户的角色
        user_role_stmt = select(UserRole.role_id).where(UserRole.user_id == current_user.guid)
        user_role_result = await db.execute(user_role_stmt)
        role_ids = [row[0] for row in user_role_result.all()]

        if not role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少 {resource}:{action} 权限"
            )

        # 查询角色对应的权限ID
        role_perm_stmt = select(RolePermission.permission_id).where(
            RolePermission.role_id.in_(role_ids)
        )
        role_perm_result = await db.execute(role_perm_stmt)
        permission_ids = [row[0] for row in role_perm_result.all()]

        if not permission_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少 {resource}:{action} 权限"
            )

        # 查询具体权限
        perm_stmt = select(Permission).where(
            Permission.id.in_(permission_ids),
            Permission.resource == resource,
            Permission.action == action,
            Permission.status == "active"
        )
        perm_result = await db.execute(perm_stmt)
        permission = perm_result.scalar_one_or_none()

        if permission is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少 {resource}:{action} 权限"
            )

        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"权限检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="权限检查服务暂时不可用"
        )

async def require_permissions(
    permissions: List[tuple],  # [(resource, action), ...]
    require_all: bool = True,  # True: 需要所有权限, False: 满足任一权限即可
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    多权限检查依赖项
    :param permissions: 权限列表 [(resource, action), ...]
    :param require_all: 是否需要所有权限
    :param current_user: 当前用户
    :param db: 数据库会话
    :return: 如果有权限则返回True，否则抛出异常
    """
    # 超级用户检查
    if current_user.is_superuser:
        return True

    try:
        # 查询用户的角色
        user_role_stmt = select(UserRole.role_id).where(UserRole.user_id == current_user.guid)
        user_role_result = await db.execute(user_role_stmt)
        role_ids = [row[0] for row in user_role_result.all()]

        if not role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="缺少必要的权限"
            )

        # 查询角色对应的权限ID
        role_perm_stmt = select(RolePermission.permission_id).where(
            RolePermission.role_id.in_(role_ids)
        )
        role_perm_result = await db.execute(role_perm_stmt)
        permission_ids = [row[0] for row in role_perm_result.all()]

        if not permission_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="缺少必要的权限"
            )

        satisfied_count = 0
        for resource, action in permissions:
            # 查询具体权限
            perm_stmt = select(Permission).where(
                Permission.id.in_(permission_ids),
                Permission.resource == resource,
                Permission.action == action,
                Permission.status == "active"
            )
            perm_result = await db.execute(perm_stmt)
            permission = perm_result.scalar_one_or_none()

            if permission is not None:
                satisfied_count += 1
                if not require_all:  # 满足任一权限即可
                    return True

        if require_all and satisfied_count != len(permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="缺少必要的权限"
            )

        if not require_all and satisfied_count == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="缺少任一所需权限"
            )

        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"多权限检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="权限检查服务暂时不可用"
        )
