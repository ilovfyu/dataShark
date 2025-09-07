from functools import wraps
from typing import Callable


from backend.common.resp_schema import RespCall
from backend.decorators.auth_decorator import require_auth, require_superuser, optional_auth
from backend.decorators.permission_decorator import require_permission, require_permissions

def auth_and_permission(
    resource: str,
    action: str,
    check_superuser: bool = True
):
    """
    认证和权限检查组合装饰器
    """
    def decorator(func: Callable):
        # 先应用认证装饰器，再应用权限装饰器
        func = require_auth()(func)
        func = require_permission(resource, action, check_superuser)(func)
        return func
    return decorator

def optional_auth_and_permission(
    resource: str,
    action: str,
    check_superuser: bool = True
):
    """
    可选认证和权限检查组合装饰器
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取request对象
            request = None
            for arg in args:
                if hasattr(arg, 'state'):
                    request = arg
                    break

            if request is None:
                for key, value in kwargs.items():
                    if hasattr(value, 'state'):
                        request = value
                        break

            if request is None:
                return await func(*args, **kwargs)

            # 尝试认证（但不强制）
            try:
                # 这里可以复用认证逻辑的一部分
                from backend.utils.jwt import decode_access_token
                from sqlalchemy.ext.asyncio import AsyncSession
                from sqlalchemy import select
                from backend.core.db.mysql import get_db
                from backend.models.rbac import User

                auth_header = request.headers.get("Authorization")
                if auth_header:
                    try:
                        scheme, token = auth_header.split()
                        if scheme.lower() == "bearer":
                            payload = decode_access_token(token)
                            if payload:
                                user_id = payload.get("sub")
                                if user_id:
                                    db_gen = get_db()
                                    db_session: AsyncSession = await db_gen.__anext__()
                                    try:
                                        stmt = select(User).where(User.guid == user_id)
                                        result = await db_session.execute(stmt)
                                        user = result.scalar_one_or_none()
                                        if user and user.status == "active":
                                            request.state.current_user = user
                                            request.state.user_id = user_id
                                    finally:
                                        await db_session.close()
                    except Exception:
                        pass  # 认证失败不影响继续执行

            except Exception:
                pass  # 忽略认证过程中的任何错误

            # 检查用户是否已认证
            current_user = getattr(request.state, 'current_user', None)
            if current_user is None:
                # 未认证用户无权限访问
                return RespCall.fail(
                    message="需要认证才能访问此资源",
                    code=401,
                    request=request,
                )

            # 超级用户检查
            if check_superuser and current_user.is_superuser:
                return await func(*args, **kwargs)

            # 检查用户权限
            if not current_user.has_permission([], resource, action):
                return RespCall.fail(
                    message=f"缺少 {resource}:{action} 权限",
                    code=403,
                    request=request,
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
