from fastapi import APIRouter, Request, Depends
from backend.common.resp_schema import RespCall
from backend.decorators.auth_decorator import require_auth
from backend.dto.workspace_dto import (
    WorkspaceCreateReqDto, WorkspaceDeleteReqDto, WorkspaceUpdateReqDto, WorkspaceQueryListReqDto,
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

@workspace_router.put("/workspace", summary="更新工作空间")
async def workspace_update_api(request: Request, req: WorkspaceUpdateReqDto, db: AsyncSession = Depends(get_db)):
    try:
        pass
    except Exception as err:
        raise err

@workspace_router.get("/workspace", summary="删除工作空间")
async def workspace_list_api(request: Request, db: AsyncSession = Depends(get_db)):
    req : WorkspaceQueryListReqDto = WorkspaceQueryListReqDto(

    )
    try:
        pass
    except Exception as err:
        raise err


@workspace_router.delete("/workspace", summary="创建工作空间")
async def workspace_delete_api(request: Request, req: WorkspaceDeleteReqDto, db: AsyncSession = Depends(get_db)):
    try:
        resp = await workspace_service.workspace_delete(req, db)
        return RespCall.success(
            data=resp,
            request=request,
        )
    except Exception as err:
        raise err

