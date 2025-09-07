import re
from datetime import datetime
from pydantic import Field, BaseModel, field_validator
from backend.constants.model_constant import UserStatusEnum, RoleStatusEnum, RoleTypeEnum
from backend.dto.base import BaseSchema, BasePageReq, BasePageResp
from typing import Optional, List


class UserCreateReq(BaseSchema):
    username: str = Field(..., description="用户名", example="admin", max_length=50, min_length=3)
    password: str = Field(..., description="密码", example="123456", max_length=50, min_length=6)


class UserCreateResp(BaseSchema):
    guid: str = Field(..., description="用户guid")




class UserDeleteReq(BaseSchema):
    guids: List[str] = Field(..., description="guid列表")




class UserBase(BaseSchema):
    avatar_url: str = Field(None, description="用户头像")
    nickname: str = Field(None, description="用户昵称")
    email: str = Field(None, description="用户邮箱")
    phone: str  = Field(None, description="用户手机")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, v):
                raise ValueError('邮箱格式不正确')
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            phone_regex = r'^1[3-9]\d{9}$'
            if not re.match(phone_regex, v):
                raise ValueError('手机号格式不正确')
        return v




class UserUpdateReq(UserBase):
    guid: str = Field(..., description="用户guid")



class UserQueryListReq(BasePageReq):
    status: Optional[UserStatusEnum] = Field(None, description="用户状态")



class LoginReq(BaseSchema):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")



class LoginResp(BaseSchema):
    access_token: str = Field(..., description="访问令牌")



class UserUpdateRoleReq(BaseSchema):
    pass



class RoleListReq(BasePageReq):
    status: Optional[RoleStatusEnum] = Field(None, description="角色状态")
    role_type: Optional[RoleTypeEnum] = Field(None, description="角色类型")




class QueryUserRoleListReq(BasePageReq):
    guid: str = Field(..., description="用户guid")




class QueryRoleModel(BaseSchema):
    role_name: str = Field(..., description="角色名称")
    role_type: RoleTypeEnum = Field(..., description="角色类型")
    status: RoleStatusEnum = Field(..., description="角色状态")
    description: str = Field(None, description="角色描述")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")



class QueryUserRoleListResp(BasePageResp):
    guid: str = Field(..., description="用户guid")
    username: str = Field(..., description="用户名")




class UpdateUserRoleReq(BaseSchema):
    pass



