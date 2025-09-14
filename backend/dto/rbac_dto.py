from datetime import datetime
from pydantic import Field
from backend.constants.model_constant import UserStatusEnum, RoleTypeEnum, RoleStatusEnum, PermissionActionEnum, \
    PermissionTypeEnum, PermissionStatusEnum, HttpMethodEnum, PermissionResourceEnum
from backend.dto.base import BasePageReqDto, BaseSchema
from typing import Optional, List


class UserCreateReqDto(BaseSchema):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    email: str = Field(None, description="邮箱")
    phone: str = Field(None, description="手机号")
    nickname: str = Field(None, description="昵称")
    avatar_url: str = Field(None, description="头像")



class UserDeleteReqDto(BaseSchema):
    guids: List[str] = Field(..., description="用户guid列表")



class UserUpdateReqDto(BaseSchema):
    guid: str = Field(..., description="用户guid")
    username: str = Field(None, description="用户名")
    nickname: str = Field(None, description="昵称")
    email: str = Field(None, description="邮箱")
    phone: str = Field(None, description="手机号")
    avatar_url: str = Field(None, description="头像url")



class UserQueryListReqDto(BasePageReqDto):
    status: Optional[UserStatusEnum] = Field(UserStatusEnum.ACTIVE, description="状态")
    start_login_time: datetime = Field(None, description="开始登录时间")
    end_login_time: datetime = Field(None, description="结束登录时间")




class LoginReqDto(BaseSchema):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    email: str = Field(None, description="邮箱")
    phone: str = Field(None, description="手机号")
    ip: str = Field(None, description="登录ip")




class LoginRespDto(BaseSchema):
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(..., description="令牌类型")



class UserStatusReqDto(BaseSchema):
    guid: str = Field(..., description="用户guid")
    status: UserStatusEnum = Field(..., description="用户状态")



class UserChangePasswordReqDto(BaseSchema):
    guid: str = Field(..., description="用户guid")
    password: str = Field(..., description="用户密码")




class RoleCreateReqDto(BaseSchema):
    name: str = Field(..., description="角色名称")
    description: str = Field(..., description="角色描述")
    role_type: RoleTypeEnum = Field(default=RoleTypeEnum.SYSTEM, description="角色类型")
    status: RoleStatusEnum = Field(default=RoleStatusEnum.ACTIVE, description="角色状态")



class RoleUpdateReqDto(BaseSchema):
    id: int = Field(..., description="角色id")
    name: str = Field(..., description="角色名称")
    description: str = Field(..., description="角色描述")
    status: RoleStatusEnum = Field(default=RoleStatusEnum.ACTIVE, description="角色状态")
    role_type: RoleTypeEnum = Field(default=RoleTypeEnum.SYSTEM, description="角色类型")


class RoleDeleteReqDto(BaseSchema):
    id: List[int] = Field(..., description="角色ID列表")


class RoleListReqDto(BasePageReqDto):
    status: Optional[RoleStatusEnum] = Field(None, description="角色状态")
    role_type: Optional[RoleTypeEnum] = Field(None, description="角色类型")




class CreatePermissionReqDto(BaseSchema):
    name: str = Field(..., description="权限名称")
    description: str = Field(None, description="权限描述")
    resource: PermissionResourceEnum = Field(..., description="权限资源")
    action: PermissionActionEnum = Field(..., description="权限操作")
    permission_type: PermissionTypeEnum = Field(PermissionTypeEnum.API, description="权限类型")
    status: PermissionStatusEnum = Field(PermissionStatusEnum.ACTIVE, description="权限状态")
    level: int = Field(1, description="权限等级")
    api_endpoint: str = Field(None, description="api端点")
    http_method: HttpMethodEnum = Field(None, description="http方法")





class UpdatePermissionReqDto(BaseSchema):
    id: int = Field(..., description="权限id")
    name: str = Field(None, description="权限名称")
    description: str = Field(None, description="权限描述")
    resource: PermissionResourceEnum = Field(None, description="权限资源")
    action: PermissionActionEnum = Field(None, description="权限操作")
    permission_type: PermissionTypeEnum = Field(None, description="权限类型")
    status: PermissionStatusEnum = Field(None, description="权限状态")
    level: int = Field(None, description="权限等级")
    api_endpoint: str = Field(None, description="api端点")
    http_method: HttpMethodEnum = Field(None, description="http方法")



class QueryPermissionListReqDto(BasePageReqDto):
    action: Optional[PermissionActionEnum] = Field(None, description="权限动作")
    resource: Optional[PermissionResourceEnum] = Field(None, description="权限资源")
    status: Optional[PermissionStatusEnum] = Field(None, description="权限状态")
    level: Optional[int] = Field(None, description="权限等级")
    http_method: Optional[HttpMethodEnum] = Field(None, description="http方法")




class DeletePermissionReqDto(BaseSchema):
    ids: List[int] = Field(..., description="权限id")
