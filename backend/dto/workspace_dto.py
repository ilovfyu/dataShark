import json
from typing import Optional
from pydantic import Field
from backend.constants.model_constant import WorkSpaceStatusEnum
from backend.dto.base import BaseSchema, BasePageReqDto




class WorkspaceCreateReqDto(BaseSchema):
    name: str = Field(..., description="工作空间名称")
    description: str = Field(..., description="工作空间描述")
    config: dict = Field(None, description="工作空间配置信息Json")




class WorkspaceUpdateReqDto(BaseSchema):
    code: str = Field(..., description="工作空间编码")
    config: str = Field(None, description="工作空间配置信息Json")
    description: str = Field(None, description="工作空间描述")
    status: Optional[WorkSpaceStatusEnum] = Field(None, description="工作空间状态")



class WorkspaceQueryListReqDto(BasePageReqDto):
    status: Optional[WorkSpaceStatusEnum] = Field(None, description="工作空间状态")



class WorkspaceDeleteReqDto(BaseSchema):
    code: str = Field(..., description="工作空间编码")



