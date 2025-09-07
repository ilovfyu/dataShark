from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.common.resp_schema import RespCall
from backend.constants.model_constant import UserStatusEnum, RoleStatusEnum, RoleTypeEnum
from backend.core.db.mysql import get_db
from backend.decorators.auth_decorator import require_auth
from backend.dto.rbac import (
    UserCreateReq, UserDeleteReq, UserUpdateReq, UserQueryListReq, LoginReq, RoleListReq, QueryUserRoleListReq,
)
from backend.services.rbac_service import rbac_service
from backend.core.logs.loguru_config import Logger

logger = Logger.get_logger()
rbac_router = APIRouter(prefix="/rbac")



@rbac_router.post("/user", summary="创建用户")
async def create_user(request: Request, data: UserCreateReq, db: AsyncSession = Depends(get_db)):
    try:
        result = await rbac_service.create_user(data, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err


@rbac_router.delete("/user", summary="删除用户")
@require_auth()
async def delete_user(request: Request, data: UserDeleteReq, db: AsyncSession = Depends(get_db)):
    try:
        result = await rbac_service.delete_user(data, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err



@rbac_router.put("/user", summary="更新用户")
@require_auth()
async def update_user(request: Request, req: UserUpdateReq, db: AsyncSession = Depends(get_db)):
    try:
        result = await rbac_service.update_user(req, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err



@rbac_router.get("/user/{guid}", summary="查询用户详情")
@require_auth()
async def query_user_detail(request: Request, guid: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await rbac_service.query_user_detail(guid, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err



@rbac_router.get("/user", summary="查询用户列表")
@require_auth()
async def query_user_list(
        request: Request,
        page: int = Query(1, description="页码"),
        page_size: int = Query(10, description="每页数量"),
        status: Optional[UserStatusEnum] = Query(UserStatusEnum.ACTIVE, description="状态"),
        db: AsyncSession = Depends(get_db)):
    try:
        req = UserQueryListReq(
            page=page,
            page_size=page_size,
            status=status
        )
        result = await rbac_service.query_user_list(req, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err



@rbac_router.post("/login", summary="用户登录")
async def Login(request: Request, req: LoginReq, db: AsyncSession = Depends(get_db)):
    try:
        result = await rbac_service.login_user(req, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err





@rbac_router.get("/readme", summary="获取当前用户信息")
@require_auth()
async def get_current_user_info(request: Request):
    user = request.state.current_user
    try:
        result = await rbac_service.get_current_user_info(user)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err



@rbac_router.get("/role", summary="获取角色列表")
async def get_role_list(
        request: Request,
        page: int = Query(1, description="页码"),
        page_size: int = Query(10, description="每页数量"),
        status: Optional[RoleStatusEnum] = Query(UserStatusEnum.ACTIVE, description="状态"),
        role_Type: Optional[RoleTypeEnum] = Query(RoleTypeEnum.SYSTEM, description="角色类型"),
        db: AsyncSession = Depends(get_db)
):
    req = RoleListReq(
        page=page,
        page_size=page_size,
        status=status,
        role_type=role_Type
    )
    try:
        result = await rbac_service.query_role_list(req, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err




@rbac_router.get("/user/{guid}/roles", summary="查询用户角色列表")
async def get_user_role_list(
        request: Request,
        guid: str,
        db: AsyncSession = Depends(get_db),
        page: int = Query(1, description="页码"),
        page_size: int = Query(10, description="每页数量")
):
    try:
        req = QueryUserRoleListReq(page=page, page_size=page_size, guid=guid)
        result = await rbac_service.query_user_role_list(req, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err