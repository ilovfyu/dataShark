from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.common.resp_schema import RespCall
from backend.constants.model_constant import UserStatusEnum, RoleStatusEnum, RoleTypeEnum, PermissionStatusEnum, \
    PermissionActionEnum, HttpMethodEnum, PermissionResourceEnum, PermissionGroupStatusEnum
from backend.core.framework.mysql import get_db
from backend.decorators.auth_decorator import require_auth, require_superuser
from backend.dto.rbac_dto import (
    UserCreateReqDto, LoginReqDto, UserUpdateReqDto, UserQueryListReqDto, UserStatusReqDto, UserChangePasswordReqDto,
    UserDeleteReqDto, RoleCreateReqDto, RoleUpdateReqDto, RoleDeleteReqDto, RoleListReqDto, CreatePermissionReqDto,
    UpdatePermissionReqDto, QueryPermissionListReqDto, DeletePermissionReqDto, PermissionGroupCreateReqDto,
    PermissionGroupUpdateReqDto, PermissionGroupDeleteReqDto, PermissionGroupListReqDto, UserRoleAssignReqDto,
    RolePermissionAssignReqDto, RolePermissionGroupAssignReqDto, UserWorkspaceAssignReqDto, GroupPermissionAssignReqDto
)
from backend.services.rbac_service import rbac_service
from backend.utils.message_utils import MessageUtils
from backend.utils.model_utils import ModelConverter

rbac_router = APIRouter(prefix="/rbac", tags=["RBAC"])


@rbac_router.post("/user", summary="创建用户")
async def create_user_api(request: Request, data: UserCreateReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await rbac_service.create_user(data, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as e:
        raise


@rbac_router.post("/user/login", summary="用户登录")
async def login_user_api(request: Request, data: LoginReqDto, db: AsyncSession = Depends(get_db)):
    try:
        data.ip = MessageUtils.get_client_ip(request)
        resp = await rbac_service.login(data, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as e:
        raise



@rbac_router.put("/user", summary="更新用户")
@require_auth()
async def update_user_api(request: Request, data: UserUpdateReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await rbac_service.update_user(data, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as e:
        raise



@rbac_router.get("/user", summary="查询用户列表")
@require_auth()
async def query_user_list_api(
        request: Request,
        status: Optional[UserStatusEnum] = Query(None, description="状态"),
        start_time: Optional[datetime] = Query(None, description="开始时间"),
        end_time: Optional[datetime] = Query(None, description="结束时间"),
        db: AsyncSession = Depends(get_db)
):
    try:
        req = UserQueryListReqDto(
            status=status,
            start_login_time=start_time,
            end_login_time=end_time
        )
        resp = await rbac_service.query_user_list(req, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as e:
        raise



@rbac_router.get("/user/me", summary="查询当前用户")
@require_auth()
async def query_me_api(request: Request):
    current_user = getattr(request.state, "current_user")
    try:
        resp = ModelConverter.model_to_dict(current_user, exclude_fields=["hash_password"])
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as err:
        raise err


@rbac_router.get("/user/{guid}/detail", summary="查询用户详情")
@require_auth()
async def query_user_detail_api(request: Request, guid: str,  db: AsyncSession = Depends(get_db)):
    try:
        resp = await rbac_service.query_user_detail(guid, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as err:
        raise err



@rbac_router.put("/user/status", summary="修改用户状态")
@require_auth()
@require_superuser()
async def user_change_status_api(request: Request, req: UserStatusReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await rbac_service.user_change_status_api(req, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as err:
        raise err






@rbac_router.put("/user/secret", summary="修改用户密码")
@require_auth()
async def user_change_password_api(request: Request, req: UserChangePasswordReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await rbac_service.user_change_password_api(req, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as err:
        raise err



@rbac_router.delete("/user", summary="删除用户")
@require_auth()
async def delete_users_api(request: Request, req: UserDeleteReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await rbac_service.delete_user(req, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as err:
        raise err





@rbac_router.post("/role", summary="创建角色")
@require_auth()
async def create_role_api(request: Request, req: RoleCreateReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await rbac_service.create_role(req, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as err:
        raise err


@rbac_router.put("/role", summary="更新角色")
@require_auth()
async def update_role_api(request: Request, req: RoleUpdateReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await rbac_service.update_role(req, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as err:
        raise err


@rbac_router.delete("/role", summary="删除角色")
@require_auth()
async def delete_role_api(request: Request, req: RoleDeleteReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await rbac_service.delete_role(req, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as err:
        raise err


@rbac_router.get("/role", summary="查询角色列表")
@require_auth()
async def query_role_list_api(
        request: Request,
        status: Optional[RoleStatusEnum] = Query(None, description="角色状态"),
        role_type: Optional[RoleTypeEnum] = Query(None, description="角色类型"),
        db: AsyncSession = Depends(get_db)
):
    req = RoleListReqDto(
        status=status,
        role_type=role_type
    )
    try:
        resp = await rbac_service.query_role_list(req, db)
        return RespCall.success(
            data=resp,
            request=request
        )
    except Exception as err:
        raise err



@rbac_router.get("/role/{id}/detail", summary="查询角色详情")
@require_auth()
async def query_role_detail_api(request: Request, id: int, db: AsyncSession = Depends(get_db)):
    try:
        resp = await rbac_service.query_role_detail(id, db)
        return RespCall.success(
            data=resp,
            request=request
        )
    except Exception as err:
        raise err





@rbac_router.post("/permission", summary="创建权限")
@require_auth()
async def create_permission_api(request: Request, req: CreatePermissionReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await rbac_service.create_permission(req, db)
        return RespCall.success(
            data=resp,
            request=request
        )
    except Exception as err:
        raise err



@rbac_router.put("/permission", summary="更新权限")
@require_auth()
async def update_permission_api(request: Request, req: UpdatePermissionReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await rbac_service.update_permission(req, db)
        return RespCall.success(
            data=resp,
            request=request
        )
    except Exception as err:
        raise err



@rbac_router.get("/permission", summary="查询权限列表")
@require_auth()
async def query_permission_list_api(
        request: Request,
        status: Optional[PermissionStatusEnum] = Query(None, description="权限状态"),
        action: Optional[PermissionActionEnum] = Query(None, description="权限动作"),
        resource: Optional[PermissionResourceEnum] = Query(None, description="权限资源"),
        http_method: Optional[HttpMethodEnum] = Query(None, description="http方法"),
        db: AsyncSession = Depends(get_db)
):
    req = QueryPermissionListReqDto(
        action=action,
        resource=resource,
        http_method=http_method,
        status=status,
    )
    try:
        resp = await rbac_service.query_permission_list(req, db)
        return RespCall.success(
            data=resp,
            request=request
        )
    except Exception as err:
        raise err



@rbac_router.delete("/permission", summary="删除权限")
@require_auth()
async def delete_permission_api(request: Request, data: DeletePermissionReqDto, db: AsyncSession = Depends(get_db)):
    try:
        result = await rbac_service.delete_permission(data, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err




@rbac_router.post("/permission/group", summary="创建权限组")
@require_auth()
async def permission_group_create_api(request: Request, req: PermissionGroupCreateReqDto, db: AsyncSession = Depends(get_db)):
    try:
        result = await rbac_service.permission_group_create(req, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err


@rbac_router.put("/permission/group", summary="更新权限组")
@require_auth()
async def permission_group_update_api(request: Request, req: PermissionGroupUpdateReqDto, db: AsyncSession = Depends(get_db)):
    try:
        result = await rbac_service.permission_group_update(req, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err


@rbac_router.delete("/permission/group", summary="删除权限组")
@require_auth()
async def permission_group_delete_api(request: Request, req: PermissionGroupDeleteReqDto, db: AsyncSession = Depends(get_db)):
    try:
        result = await rbac_service.permission_group_delete(req, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err


@rbac_router.get("/permission/group", summary="权限组列表")
@require_auth()
async def permission_group_list_api(
        request: Request,
        status: Optional[PermissionGroupStatusEnum] = Query(PermissionGroupStatusEnum.ACTIVE, description="状态"),
        db: AsyncSession = Depends(get_db)
):
    req = PermissionGroupListReqDto(
        status=status,
    )
    try:
        result = await rbac_service.permission_group_list(req, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err




async def assign_user_role_api(request: Request, req: UserRoleAssignReqDto, db: AsyncSession = Depends(get_db)):
    pass





async def assign_role_permission_api(request: Request, req: RolePermissionAssignReqDto, db: AsyncSession = Depends(get_db)):
    pass




async def assign_role_permission_group_api(request: Request, req: RolePermissionGroupAssignReqDto, db: AsyncSession = Depends(get_db)):
    pass





async def assign_user_workspace_api(request: Request, req: UserWorkspaceAssignReqDto, db: AsyncSession = Depends(get_db)):
    pass





async def assign_permission_group_api(request: Request, req: GroupPermissionAssignReqDto, db: AsyncSession = Depends(get_db)):
    pass





async def assign_user_workspace_role_api(request: Request, req: UserRoleAssignReqDto, db: AsyncSession = Depends(get_db)):
    pass