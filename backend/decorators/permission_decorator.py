from functools import wraps
from typing import Callable, List, Optional, Union
from fastapi import HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.rbac import Permission, Role, RolePermission, UserRole, User
from backend.models.workspace import UserWorkspace
from backend.core.db.mysql import get_db
from backend.core.logs.loguru_config import Logger

logger = Logger.get_logger()

def _get_request_from_args(args, kwargs) -> Optional[Request]:
    """从函数参数中获取Request对象"""
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

    return request

async def _check_user_permission(
    user_id: str,
    resource: str,
    action: str,
    request: Request
) -> bool:
    """
    检查用户是否有指定资源和操作的权限
    :param user_id: 用户ID
    :param resource: 资源名称
    :param action: 操作名称
    :param request: 请求对象
    :return: 是否有权限
    """
    try:
        # 获取数据库会话
        db_gen = get_db()
        db_session: AsyncSession = await db_gen.__anext__()

        try:
            # 检查是否为超级用户
            user_stmt = select(User).where(User.guid == user_id)
            user_result = await db_session.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if user and user.is_superuser:
                return True

            # 获取用户的角色（包括全局角色和工作空间角色）
            role_ids = set()

            # 获取全局角色
            user_role_stmt = select(UserRole.role_id).where(UserRole.user_id == user_id)
            user_role_result = await db_session.execute(user_role_stmt)
            global_role_ids = [row[0] for row in user_role_result.all()]
            role_ids.update(global_role_ids)

            # 如果请求中包含工作空间信息，获取工作空间角色
            workspace_id = getattr(request.state, 'workspace_id', None)
            if workspace_id:
                user_workspace_stmt = select(UserWorkspace.role_id).where(
                    UserWorkspace.user_id == user_id,
                    UserWorkspace.workspace_id == workspace_id,
                    UserWorkspace.is_active == True
                )
                user_workspace_result = await db_session.execute(user_workspace_stmt)
                workspace_role_ids = [row[0] for row in user_workspace_result.all()]
                role_ids.update(workspace_role_ids)

            if not role_ids:
                return False

            # 查询角色对应的权限ID
            role_perm_stmt = select(RolePermission.permission_id).where(
                RolePermission.role_id.in_(list(role_ids))
            )
            role_perm_result = await db_session.execute(role_perm_stmt)
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
            perm_result = await db_session.execute(perm_stmt)
            permission = perm_result.scalar_one_or_none()

            return permission is not None
        finally:
            await db_session.close()
    except Exception as e:
        logger.error(f"检查用户权限时出错: {str(e)}")
        return False

async def _check_user_permission_by_code(
    user_id: str,
    permission_code: str,
    request: Request
) -> bool:
    """
    通过权限代码检查用户权限
    :param user_id: 用户ID
    :param permission_code: 权限代码
    :param request: 请求对象
    :return: 是否有权限
    """
    try:
        # 获取数据库会话
        db_gen = get_db()
        db_session: AsyncSession = await db_gen.__anext__()

        try:
            # 检查是否为超级用户
            user_stmt = select(User).where(User.guid == user_id)
            user_result = await db_session.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if user and user.is_superuser:
                return True

            # 获取用户的角色（包括全局角色和工作空间角色）
            role_ids = set()

            # 获取全局角色
            user_role_stmt = select(UserRole.role_id).where(UserRole.user_id == user_id)
            user_role_result = await db_session.execute(user_role_stmt)
            global_role_ids = [row[0] for row in user_role_result.all()]
            role_ids.update(global_role_ids)

            # 如果请求中包含工作空间信息，获取工作空间角色
            workspace_id = getattr(request.state, 'workspace_id', None)
            if workspace_id:
                user_workspace_stmt = select(UserWorkspace.role_id).where(
                    UserWorkspace.user_id == user_id,
                    UserWorkspace.workspace_id == workspace_id,
                    UserWorkspace.is_active == True
                )
                user_workspace_result = await db_session.execute(user_workspace_stmt)
                workspace_role_ids = [row[0] for row in user_workspace_result.all()]
                role_ids.update(workspace_role_ids)

            if not role_ids:
                return False

            # 查询角色对应的权限ID
            role_perm_stmt = select(RolePermission.permission_id).where(
                RolePermission.role_id.in_(list(role_ids))
            )
            role_perm_result = await db_session.execute(role_perm_stmt)
            permission_ids = [row[0] for row in role_perm_result.all()]

            if not permission_ids:
                return False

            # 查询具体权限
            perm_stmt = select(Permission).where(
                Permission.id.in_(permission_ids),
                Permission.code == permission_code,
                Permission.status == "active"
            )
            perm_result = await db_session.execute(perm_stmt)
            permission = perm_result.scalar_one_or_none()

            return permission is not None
        finally:
            await db_session.close()
    except Exception as e:
        logger.error(f"通过代码检查用户权限时出错: {str(e)}")
        return False

async def _check_user_role(
    user_id: str,
    role_name: Union[str, List[str]],
    request: Request
) -> bool:
    """
    检查用户是否有指定角色
    :param user_id: 用户ID
    :param role_name: 角色名称或角色名称列表
    :param request: 请求对象
    :return: 是否有角色
    """
    try:
        # 获取数据库会话
        db_gen = get_db()
        db_session: AsyncSession = await db_gen.__anext__()

        try:
            # 检查是否为超级用户
            user_stmt = select(User).where(User.guid == user_id)
            user_result = await db_session.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if user and user.is_superuser:
                return True

            # 获取用户的角色（包括全局角色和工作空间角色）
            role_names = set()

            # 获取全局角色名称
            user_role_stmt = select(Role.name).join(UserRole, Role.id == UserRole.role_id).where(
                UserRole.user_id == user_id
            )
            user_role_result = await db_session.execute(user_role_stmt)
            global_role_names = [row[0] for row in user_role_result.all()]
            role_names.update(global_role_names)

            # 如果请求中包含工作空间信息，获取工作空间角色名称
            workspace_id = getattr(request.state, 'workspace_id', None)
            if workspace_id:
                user_workspace_stmt = select(Role.name).join(
                    UserWorkspace, Role.id == UserWorkspace.role_id
                ).where(
                    UserWorkspace.user_id == user_id,
                    UserWorkspace.workspace_id == workspace_id,
                    UserWorkspace.is_active == True,
                    Role.role_type == "workspace"  # 只检查工作空间类型的角色
                )
                user_workspace_result = await db_session.execute(user_workspace_stmt)
                workspace_role_names = [row[0] for row in user_workspace_result.all()]
                role_names.update(workspace_role_names)

            # 检查是否有匹配的角色
            if isinstance(role_name, str):
                return role_name in role_names
            else:
                return any(name in role_names for name in role_name)
        finally:
            await db_session.close()
    except Exception as e:
        logger.error(f"检查用户角色时出错: {str(e)}")
        return False

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
    角色检查装饰器（支持工作空间级别角色）
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

            # 检查用户角色（包括工作空间角色）
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

def require_workspace_role(workspace_id_param: str = "workspace_id"):
    """
    工作空间角色检查装饰器
    确保用户在指定工作空间中具有角色
    :param workspace_id_param: 请求参数中工作空间ID的名称
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
            if current_user.is_superuser:
                return await func(*args, **kwargs)

            # 获取工作空间ID
            workspace_id = None
            # 从路径参数获取
            if workspace_id_param in kwargs:
                workspace_id = kwargs[workspace_id_param]
            # 从查询参数获取
            elif workspace_id_param in request.query_params:
                workspace_id = request.query_params[workspace_id_param]
            # 从请求体获取
            elif hasattr(request, "json"):
                try:
                    body = await request.json()
                    if workspace_id_param in body:
                        workspace_id = body[workspace_id_param]
                except:
                    pass

            if not workspace_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="缺少工作空间ID参数"
                )

            # 检查用户是否在该工作空间中
            try:
                db_gen = get_db()
                db_session: AsyncSession = await db_gen.__anext__()

                try:
                    stmt = select(UserWorkspace).where(
                        UserWorkspace.user_id == current_user.guid,
                        UserWorkspace.workspace_id == workspace_id,
                        UserWorkspace.is_active == True
                    )
                    result = await db_session.execute(stmt)
                    user_workspace = result.scalar_one_or_none()

                    if not user_workspace:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="用户不在指定工作空间中或无访问权限"
                        )

                    # 将工作空间ID添加到请求状态中，供其他权限检查使用
                    request.state.workspace_id = workspace_id
                finally:
                    await db_session.close()
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"检查工作空间角色时出错: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="工作空间权限检查服务暂时不可用"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_workspace_permission(
    resource: str,
    action: str,
    workspace_id_param: str = "workspace_id",
    check_superuser: bool = True
):
    """
    工作空间权限检查装饰器
    确保用户在指定工作空间中具有特定资源和操作的权限
    :param resource: 资源名称
    :param action: 操作名称
    :param workspace_id_param: 请求参数中工作空间ID的名称
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

            # 获取工作空间ID
            workspace_id = None
            # 从路径参数获取
            if workspace_id_param in kwargs:
                workspace_id = kwargs[workspace_id_param]
            # 从查询参数获取
            elif workspace_id_param in request.query_params:
                workspace_id = request.query_params[workspace_id_param]
            # 从请求体获取
            elif hasattr(request, "json"):
                try:
                    body = await request.json()
                    if workspace_id_param in body:
                        workspace_id = body[workspace_id_param]
                except:
                    pass

            if not workspace_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="缺少工作空间ID参数"
                )

            # 检查用户是否在该工作空间中并具有相应权限
            try:
                db_gen = get_db()
                db_session: AsyncSession = await db_gen.__anext__()

                try:
                    # 检查用户是否在工作空间中
                    stmt = select(UserWorkspace).where(
                        UserWorkspace.user_id == current_user.guid,
                        UserWorkspace.workspace_id == workspace_id,
                        UserWorkspace.is_active == True
                    )
                    result = await db_session.execute(stmt)
                    user_workspace = result.scalar_one_or_none()

                    if not user_workspace:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="用户不在指定工作空间中或无访问权限"
                        )

                    # 将工作空间ID添加到请求状态中，供权限检查使用
                    request.state.workspace_id = workspace_id

                    # 检查工作空间级别的权限
                    has_perm = await _check_user_permission(current_user.guid, resource, action, request)
                    if not has_perm:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"缺少在工作空间 {workspace_id} 中的 {resource}:{action} 权限"
                        )
                finally:
                    await db_session.close()
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"检查工作空间权限时出错: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="工作空间权限检查服务暂时不可用"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
