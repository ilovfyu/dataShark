from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from backend.common.resp_schema import RespCall
from backend.constants.model_constant import WorkSpaceStatusEnum
from backend.decorators.auth_decorator import require_auth
from backend.dto.workspace_dto import (
    WorkspaceCreateReqDto, WorkspaceDeleteReqDto, WorkspaceUpdateReqDto, WorkspaceQueryListReqDto,
    ResourceGroupCreateReqDto, ResourceGroupDeleteReqDto, ResourceGroupQueryListReqDto,
)
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.framework.mysql import get_db
from backend.services.workspace_service import workspace_service
workspace_router = APIRouter(prefix="/wksp", tags=["workspace"])



@workspace_router.post("/workspace", summary="创建工作空间")
@require_auth()
async def workspace_create_api(request: Request, req: WorkspaceCreateReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await workspace_service.workspace_create(request, req, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as err:
        raise err

@workspace_router.put("/{workspace_id}/workspace", summary="更新工作空间")
async def workspace_update_api(request: Request, workspace_id: str, req: WorkspaceUpdateReqDto, db: AsyncSession = Depends(get_db)):
    try:
        result = await workspace_service.workspace_update(workspace_id, req, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err


@workspace_router.get("/workspace", summary="查询工作空间")
async def workspace_list_api(
        request: Request,
        status: Optional[WorkSpaceStatusEnum] = Query(None, description="状态"),
        db: AsyncSession = Depends(get_db)
):
    req = WorkspaceQueryListReqDto(
        status=status,
    )
    try:
        result = await workspace_service.workspace_list(req, db)
        return RespCall.success(
            data=result,
            request=request,
        )
    except Exception as err:
        raise err


@workspace_router.delete("/workspace", summary="删除工作空间")
async def workspace_delete_api(request: Request, req: WorkspaceDeleteReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await workspace_service.workspace_delete(req, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as err:
        raise err



@workspace_router.post("/resource_group", summary="创建资源组")
async def create_resource_group(request: Request, req: ResourceGroupCreateReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await workspace_service.create_resource_group(req, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as err:
        raise err




@workspace_router.delete("/resource_group", summary="删除资源组")
async def delete_resource_group(request: Request, req: ResourceGroupDeleteReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await workspace_service.delete_resource_group(req, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as err:
        raise err



@workspace_router.get("/resource_group", summary="查询资源组")
async def resource_group_query_list(
        request: Request,
        workspace_code: Optional[str] = Query("", description="工作空间编码"),
        db: AsyncSession = Depends(get_db)
):
    req = ResourceGroupQueryListReqDto(
        workspace_code=workspace_code,
    )
    try:
        resp = await workspace_service.list_resource_group(req, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as err:
        raise err