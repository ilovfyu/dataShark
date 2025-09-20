from fastapi import Request
from backend.common.errors import ErrorCode, BussinessCode
from backend.common.exception_handler import BusinessException
from backend.core.settings.config import get_settings
from backend.core.settings.config_handler import ConfigHandler
from backend.dto.base import NoneDataUnionResp
from backend.dto.workspace_dto import (
    WorkspaceCreateReqDto, WorkspaceUpdateReqDto, WorkspaceDeleteReqDto, WorkspaceQueryListReqDto,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, text
from backend.models.workspace import Workspace
from backend.core.container import get_kubernetes_client


confi = get_settings()

client = get_kubernetes_client(in_cluster=False)

class WorkspaceService:


    async def workspace_create(self, request: Request,  req: WorkspaceCreateReqDto, db: AsyncSession):
        try:
            stmt = select(Workspace).where(Workspace.name == req.name)
            result = await db.execute(stmt)
            workspace = result.scalar_one_or_none()
            if workspace:
                raise BusinessException(
                    message="工作空间已存在",
                    status_code=ErrorCode.BAD_REQUEST,
                    code=BussinessCode.EXIST_ERROR.code,
                )
            ## 创建一个数据库
            await db.execute(text(f"CREATE DATABASE IF NOT EXISTS {req.name};"))

            workspace = Workspace(
                name=req.name,
                description=req.description,
                config=req.config,
                database_url=f"mysql+aiomysql://{confi.db_username}:{confi.db_password}@{confi.db_host}:{confi.db_port}/{req.name}",
                owner_id=getattr(request.state, 'user_id'),

            )
            db.add(workspace)
            await db.commit()
            await db.refresh(workspace)

            labels = ConfigHandler.k8s_handler(req.config, "labels")
            client.create_namespace(name=workspace.code, labels=labels)

            return NoneDataUnionResp(
                pong=f"{workspace.code}"
            )
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"创建工作空间失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
            )



    async def workspace_update(self, req: WorkspaceUpdateReqDto, db: AsyncSession):
        pass




    async def workspace_delete(self, req: WorkspaceDeleteReqDto, db: AsyncSession):
        try:
            stmt = select(Workspace).where(Workspace.code == req.code)
            result = await db.execute(stmt)
            workspace = result.scalar_one_or_none()
            if not workspace:
                raise BusinessException(
                    message="工作空间不存在",
                    status_code=ErrorCode.BAD_REQUEST,
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                )
            ## todo
            client.delete_namespace(name=workspace.name)
            delete_stmt = delete(Workspace).where(Workspace.code == req.code)
            await db.execute(delete_stmt)
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"删除工作空间失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
            )




    async def workspace_list(self, req: WorkspaceQueryListReqDto, db: AsyncSession):
        pass




    async def workspace_update_config(self):
        pass



workspace_service = WorkspaceService()
