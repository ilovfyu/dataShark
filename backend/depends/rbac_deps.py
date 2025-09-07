from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.common.errors import ErrorCode
from backend.core.db.mysql import get_db
from backend.models.rbac import User
from backend.utils.jwt import decode_access_token
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
