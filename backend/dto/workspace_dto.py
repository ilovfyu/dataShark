import json
from typing import Optional, Dict
from pydantic import Field
from backend.constants.model_constant import WorkSpaceStatusEnum
from backend.dto.base import BaseSchema, BasePageReqDto
from backend.dto.k8s_config_dto import K8SConfigBase




class WorkspaceCreateReqDto(BaseSchema):
    name: str = Field(..., description="工作空间名称")
    description: str = Field(..., description="工作空间描述")
    config: K8SConfigBase = Field(None, description="工作空间配置信息Json")




class WorkspaceUpdateReqDto(BaseSchema):
    config: K8SConfigBase = Field(None, description="工作空间配置信息Json")
    description: str = Field(None, description="工作空间描述")
    status: Optional[WorkSpaceStatusEnum] = Field(None, description="工作空间状态")



class WorkspaceQueryListReqDto(BasePageReqDto):
    status: Optional[WorkSpaceStatusEnum] = Field(None, description="工作空间状态")



class WorkspaceDeleteReqDto(BaseSchema):
    code: str = Field(..., description="工作空间编码")





class ResourceGroupCreateReqDto(BaseSchema):
    name: str = Field(..., description="资源组名称")
    description: str = Field(..., description="资源组描述")
    workspace_id: str = Field(..., description="所属工作空间ID")
    cpu_limit: Optional[str] = Field(None, description="CPU限制 (如: '1000m', '1')")
    cpu_request: Optional[str] = Field(None, description="CPU请求 (如: '500m', '0.5')")
    memory_limit: Optional[str] = Field(None, description="内存限制 (如: '1Gi', '512Mi')")
    memory_request: Optional[str] = Field(None, description="内存请求 (如: '512Mi', '256Mi')")
    storage_limit: Optional[str] = Field(None, description="存储限制 (如: '10Gi', '5Gi')")
    storage_request: Optional[str] = Field(None, description="存储请求 (如: '5Gi', '2Gi')")
    replicas: Optional[int] = Field(None, description="默认副本数")
    custom_resources: Optional[Dict[str, str]] = Field(None, description="自定义资源配额")
    labels: Optional[Dict[str, str]] = Field(None, description="标签")



class ResourceGroupUpdateReqDto(BaseSchema):
    code: str = Field(..., description="资源组编码")
    name: Optional[str] = Field(None, description="资源组名称")
    description: Optional[str] = Field(None, description="资源组描述")
    cpu_limit: Optional[str] = Field(None, description="CPU限制")
    cpu_request: Optional[str] = Field(None, description="CPU请求")
    memory_limit: Optional[str] = Field(None, description="内存限制")
    memory_request: Optional[str] = Field(None, description="内存请求")
    storage_limit: Optional[str] = Field(None, description="存储限制")
    storage_request: Optional[str] = Field(None, description="存储请求")
    replicas: Optional[int] = Field(None, description="默认副本数")
    custom_resources: Optional[Dict[str, str]] = Field(None, description="自定义资源配额")
    labels: Optional[Dict[str, str]] = Field(None, description="标签")



class ResourceGroupDeleteReqDto(BaseSchema):
    code: str = Field(..., description="资源组编码")



class ResourceGroupQueryListReqDto(BasePageReqDto):
    workspace_code: str = Field(None, description="工作空间编码")




class ResourceGroupDetailReqDto(BaseSchema):
    code: str = Field(..., description="资源组编码")







