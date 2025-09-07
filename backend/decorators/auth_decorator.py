from functools import wraps
from typing import Callable, Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.core.db.mysql import get_db
from backend.models.rbac import User
from backend.utils.jwt import decode_access_token
from backend.core.logs.loguru_config import Logger

logger = Logger.get_logger()
security = HTTPBearer()

def require_auth(skip_on_failure: bool = False):
    """
    认证装饰器
    :param skip_on_failure: 认证失败时是否跳过而不是抛出异常
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取request对象
            request = None
            for arg in args:
                if hasattr(arg, 'state'):  # FastAPI Request对象
                    request = arg
                    break

            if request is None:
                # 尝试从kwargs中获取
                for key, value in kwargs.items():
                    if hasattr(value, 'state'):
                        request = value
                        break

            if request is None:
                if skip_on_failure:
                    return await func(*args, **kwargs)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="无法获取请求对象"
                    )

            try:
                # 从请求头获取令牌
                auth_header = request.headers.get("Authorization")
                if not auth_header:
                    if skip_on_failure:
                        return await func(*args, **kwargs)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="未提供认证令牌",
                            headers={"WWW-Authenticate": "Bearer"},
                        )

                try:
                    scheme, token = auth_header.split()
                    if scheme.lower() != "bearer":
                        raise ValueError("Invalid scheme")
                except ValueError:
                    if skip_on_failure:
                        return await func(*args, **kwargs)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="无效的认证头格式",
                            headers={"WWW-Authenticate": "Bearer"},
                        )

                # 解码JWT令牌
                payload = decode_access_token(token)
                if payload is None:
                    if skip_on_failure:
                        return await func(*args, **kwargs)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="无效的认证令牌",
                            headers={"WWW-Authenticate": "Bearer"},
                        )

                # 获取用户ID
                user_id: str = payload.get("sub")
                if not user_id:
                    if skip_on_failure:
                        return await func(*args, **kwargs)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="无效的认证令牌",
                            headers={"WWW-Authenticate": "Bearer"},
                        )

                # 查询用户
                db_gen = get_db()
                db_session: AsyncSession = await db_gen.__anext__()
                try:
                    stmt = select(User).where(User.guid == user_id)
                    result = await db_session.execute(stmt)
                    user = result.scalar_one_or_none()

                    if user is None:
                        if skip_on_failure:
                            return await func(*args, **kwargs)
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="用户不存在",
                                headers={"WWW-Authenticate": "Bearer"},
                            )

                    # 检查用户状态
                    if user.status != "active":
                        if skip_on_failure:
                            return await func(*args, **kwargs)
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail="用户账户已被禁用"
                            )

                    # 将用户信息添加到请求状态中
                    request.state.current_user = user
                    request.state.user_id = user_id

                finally:
                    await db_session.close()

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"认证装饰器错误: {str(e)}")
                if skip_on_failure:
                    return await func(*args, **kwargs)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="认证服务暂时不可用",
                    )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_superuser():
    """
    超级用户认证装饰器
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取request对象
            request = None
            for arg in args:
                if hasattr(arg, 'state'):  # FastAPI Request对象
                    request = arg
                    break

            if request is None:
                # 尝试从kwargs中获取
                for key, value in kwargs.items():
                    if hasattr(value, 'state'):
                        request = value
                        break

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

            # 检查是否为超级用户
            if not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="需要超级用户权限"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

# def optional_auth():
#     """
#     可选认证装饰器
#     """
#     def decorator(func: Callable):
#         @wraps(func)
#         async def wrapper(*args, **kwargs):
#             # 获取request对象
#             request = None
#             for arg in args:
#                 if hasattr(arg, 'state'):  # FastAPI Request对象
#                     request = arg
#                     break
#
#             if request is None:
#                 # 尝试从kwargs中获取
#                 for key, value in kwargs.items():
#                     if hasattr(value, 'state'):
#                         request = value
#                         break
#
#             if request is None:
#                 return await func(*args, **kwargs)
#
#             try:
#                 # 从请求头获取令牌
#                 auth_header = request.headers.get("Authorization")
#                 if not auth_header:
#                     return await func(*args, **kwargs)
#
#                 try:
#                     scheme, token = auth_header.split()
#                     if scheme.lower() != "bearer":
#                         return await func(*args, **kwargs)
#                 except ValueError:
#                     return await func(*args, **kwargs)
#
#                 # 解码JWT令牌
#                 payload = decode_access_token(token)
#                 if payload is None:
#                     return await func(*args, **kwargs)
#
#                 # 获取用户ID
#                 user_id: str = payload.get("sub")
#                 if not user_id:
#                     return await func(*args, **kwargs)
#
#                 # 查询用户
#                 db_gen = get_db()
#                 db_session: AsyncSession = await db_gen.__anext__()
#                 try:
#                     stmt = select(User).where(User.guid == user_id)
#                     result = await db_session.execute(stmt)
#                     user = result.scalar_one_or_none()
#
#                     if user is None:
#                         return await func(*args, **kwargs)
#
#                     # 检查用户状态
#                     if user.status != "active":
#                         return await func(*args, **kwargs)
#
#                     # 将用户信息添加到请求状态中
#                     request.state.current_user = user
#                     request.state.user_id = user_id
#
#                 finally:
#                     await db_session.close()
#
#             except Exception as e:
#                 logger.error(f"可选认证装饰器错误: {str(e)}")
#                 # 即使认证失败也继续执行函数
#                 pass
#
#             return await func(*args, **kwargs)
#         return wrapper
#     return decorator
