from functools import wraps
from typing import Callable, List, Optional
from fastapi import HTTPException, status
from backend.models.rbac import Permission

def require_permission(
    resource: str,
    action: str,
    check_superuser: bool = True
):
    """
    权限检查装饰器
    :param resource: 资源名称
    :param action: 操作名称
    :param check_superuser: 是否检查超级用户权限
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

            # 超级用户检查
            if check_superuser and current_user.is_superuser:
                return await func(*args, **kwargs)

            # 检查用户权限
            if not current_user.has_permission([], resource, action):
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

            # 超级用户检查
            if check_superuser and current_user.is_superuser:
                return await func(*args, **kwargs)

            # 检查用户权限
            satisfied_count = 0
            for resource, action in permissions:
                if current_user.has_permission([], resource, action):
                    satisfied_count += 1
                    if not require_all:  # 满足任一权限即可
                        break

            if require_all and satisfied_count != len(permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少必要的权限"
                )

            if not require_all and satisfied_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少任一所需权限"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
