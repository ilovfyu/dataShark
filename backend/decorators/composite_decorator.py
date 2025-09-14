from functools import wraps
from typing import Callable, List, Union
from fastapi import Request
from backend.decorators.auth_decorator import require_auth
from backend.decorators.permission_decorator import (
    require_permission,
    require_permissions,
    require_permission_by_code,
    require_role
)

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

def auth_and_permissions(
    permissions: List[tuple],
    require_all: bool = True,
    check_superuser: bool = True
):
    """
    认证和多权限检查组合装饰器
    """
    def decorator(func: Callable):
        func = require_auth()(func)
        func = require_permissions(permissions, require_all, check_superuser)(func)
        return func
    return decorator

def auth_and_role(
    role_name: Union[str, List[str]],
    check_superuser: bool = True
):
    """
    认证和角色检查组合装饰器
    """
    def decorator(func: Callable):
        func = require_auth()(func)
        func = require_role(role_name, check_superuser)(func)
        return func
    return decorator

def auth_and_permission_by_code(
    permission_code: str,
    check_superuser: bool = True
):
    """
    认证和权限代码检查组合装饰器
    """
    def decorator(func: Callable):
        func = require_auth()(func)
        func = require_permission_by_code(permission_code, check_superuser)(func)
        return func
    return decorator
