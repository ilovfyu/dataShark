import json
from fastapi import Request
from backend.common.errors import ErrorCode, BussinessCode
from backend.common.exception_handler import BusinessException
from backend.core.container.resource_quota import get_resource_quota_manager
from backend.core.settings.config import get_settings
from backend.dto.base import NoneDataUnionResp, BasePageRespDto
from backend.dto.workspace_dto import (
    WorkspaceCreateReqDto, WorkspaceUpdateReqDto, WorkspaceDeleteReqDto, WorkspaceQueryListReqDto,
    ResourceGroupCreateReqDto, ResourceGroupQueryListReqDto, ResourceGroupDetailReqDto, ResourceGroupDeleteReqDto,
    ResourceGroupUpdateReqDto,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, text, func
from backend.models.workspace import Workspace, ResourceGroup
from backend.core.container import get_kubernetes_client
from backend.utils.message_utils import MessageUtils
from backend.utils.model_utils import ModelConverter

confi = get_settings()

client = get_kubernetes_client(in_cluster=False)


class WorkspaceService:

    async def workspace_create(self, request: Request, req: WorkspaceCreateReqDto, db: AsyncSession):
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
                database_url=f"mysql+aiomysql://{confi.db_username}:{confi.db_password}@{confi.db_host}:{confi.db_port}/{req.name}",
                owner_id=getattr(request.state, 'user_id'),
                config=req.config.model_dump_json(),
                labels=ModelConverter.dict_to_json_str(req.config.labels),
            )
            db.add(workspace)
            await db.commit()
            await db.refresh(workspace)

            client.create_namespace(name=workspace.code, labels=req.config.labels)
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

    async def workspace_update(self, workspace_id: str, req: WorkspaceUpdateReqDto, db: AsyncSession):
        try:
            stmt = select(Workspace).where(Workspace.code == workspace_id)
            result = await db.execute(stmt)
            workspace: Workspace = result.scalar_one_or_none()
            if workspace is None:
                raise BusinessException(
                    message="工作空间不存在",
                    status_code=ErrorCode.BAD_REQUEST,
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                )

            field_transformers = {
                "config": lambda x: json.dumps(x),
            }
            update_model = ModelConverter.update_model_from_dto_with_transformers(
                model_instance=workspace,
                dto_instance=req,
                field_transformers=field_transformers)

            workspace.labels = ModelConverter.dict_to_json_str(req.config.labels)
            client.update_namespace(name=workspace_id, labels=req.config.labels)

            db.add(update_model)
            await db.commit()
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"更新工作空间失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
            )

    async def workspace_delete(self, req: WorkspaceDeleteReqDto, db: AsyncSession):
        try:
            stmt = select(Workspace).where(Workspace.code == req.code)
            result = await db.execute(stmt)
            workspace: Workspace = result.scalar_one_or_none()
            if not workspace:
                raise BusinessException(
                    message="工作空间不存在",
                    status_code=ErrorCode.BAD_REQUEST,
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                )
            client.delete_namespace(name=workspace.code)
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
        try:
            stmt = select(Workspace)
            count_stmt = select(func.count()).select_from(Workspace)

            if req.status:
                stmt = stmt.where(Workspace.status == req.status)
                count_stmt = count_stmt.where(Workspace.status == req.status)

            stmt = stmt.offset((req.page - 1) * req.page_size).limit(req.page_size)

            stmt_result = await db.execute(stmt)
            count_stmt_result = await db.execute(count_stmt)

            stmt_resp = stmt_result.scalars().all()
            workspace_list = ModelConverter.to_dict_list(stmt_resp, exclude_fields=["database_url"])
            total = count_stmt_result.scalar_one()
            return {
                "total": total,
                "data": workspace_list
            }
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"查询工作空间列表失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
            )

    async def create_resource_group(self, req: ResourceGroupCreateReqDto, db: AsyncSession):
        try:
            stmt = select(Workspace).where(Workspace.code == req.workspace_id)
            result = await db.execute(stmt)
            workspace: Workspace = result.scalar_one_or_none()
            if not workspace:
                raise BusinessException(
                    message="工作空间不存在",
                    status_code=ErrorCode.BAD_REQUEST,
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                )
            existing_stmt = select(ResourceGroup).where(
                ResourceGroup.name == req.name,
                ResourceGroup.workspace_id == req.workspace_id
            )
            existing_result = await db.execute(existing_stmt)
            if existing_result.scalar_one_or_none():
                raise BusinessException(
                    message="同名资源组已存在",
                    status_code=ErrorCode.BAD_REQUEST,
                    code=BussinessCode.EXIST_ERROR.code,
                )

            resource_group_code = MessageUtils.code_format(f"rg")

            resource_group = ResourceGroup(
                code=resource_group_code,
                name=req.name,
                description=req.description,
                workspace_id=req.workspace_id,
                cpu_limit=req.cpu_limit,
                cpu_request=req.cpu_request,
                memory_limit=req.memory_limit,
                memory_request=req.memory_request,
                storage_limit=req.storage_limit,
                storage_request=req.storage_request,
                replicas=req.replicas,
                custom_resources=json.dumps(req.custom_resources) if req.custom_resources else None,
                labels=json.dumps(req.labels) if req.labels else None
            )
            try:
                # k8s资源配额
                resource_quota_manager = get_resource_quota_manager()
                resource_quota_manager.apply_resource_group_quota(resource_group, workspace.code)
            except Exception as e:
                raise BusinessException(
                    message=f"资源组关联失败, {str(e)}",
                    status_code=ErrorCode.INTERNAL_SERVER_ERROR,
                    code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                )

            db.add(resource_group)
            await db.commit()
            return NoneDataUnionResp(
                pong=f"{resource_group.code}"
            )
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"创建资源组失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
            )

    async def update_resource_group(self, req: ResourceGroupUpdateReqDto, db: AsyncSession):
        try:
            pass
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"更新资源组失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
            )

    async def delete_resource_group(self, req: ResourceGroupDeleteReqDto, db: AsyncSession):
        try:
            stmt = select(ResourceGroup).where(ResourceGroup.code == req.code)
            result = await db.execute(stmt)
            resource_group = result.scalar_one_or_none()
            if not resource_group:
                raise BusinessException(
                    message="资源组不存在",
                    status_code=ErrorCode.BAD_REQUEST,
                    code=BussinessCode.NOT_EXIST_ERROR.code,
                )

            # # todo: 是否有资源在使用, 如果有资源在使用中则不能删除
            resource_quota_manager = get_resource_quota_manager()
            resource_quota_manager.remove_resource_group_quota(resource_group, resource_group.workspace_id)

            delete_stmt = delete(ResourceGroup).where(ResourceGroup.code == req.code)
            await db.execute(delete_stmt)
            return NoneDataUnionResp()
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"删除资源组失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
            )

    async def detail_resource_group(self, req: ResourceGroupDetailReqDto, db: AsyncSession):
        try:
            pass
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"查询资源组详情失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
            )

    async def list_resource_group(self, req: ResourceGroupQueryListReqDto, db: AsyncSession):
        try:
            stmt = select(ResourceGroup)
            count_stmt = select(func.count()).select_from(ResourceGroup)

            if req.workspace_code:
                stmt = stmt.where(ResourceGroup.workspace_id == req.workspace_code)
                count_stmt = count_stmt.where(ResourceGroup.workspace_id == req.workspace_code)


            stmt = stmt.offset((req.page - 1) * req.page_size).limit(req.page_size)
            result_result = await db.execute(stmt)
            resource_group_list = result_result.scalars().all()

            count_result = await db.execute(count_stmt)
            total = count_result.scalar_one()

            return BasePageRespDto(
                total=total,
                data=ModelConverter.to_dict_list(resource_group_list)
            )
        except BusinessException:
            raise
        except Exception as e:
            raise BusinessException(
                message=f"查询资源组列表失败, {str(e)}",
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
            )


workspace_service = WorkspaceService()
