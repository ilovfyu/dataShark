from pydantic import Field, BaseModel

from backend.dto.base import BaseSchema, BasePageSchema
from typing import Optional, List
from datetime import datetime
from backend.constants.model_constant import (
    UserStatusEnum,
    RoleStatusEnum,
    RoleTypeEnum,
    PermissionTypeEnum,
    PermissionActionEnum,
    PermissionStatusEnum
)



class Token(BaseSchema):
    access_token: str = Field(..., description="access token")
    token_type: str = Field("bearer", description="token type")



class TokenData(BaseSchema):
    user_id: Optional[int] = Field(None, description="user id")



class UserCreate(BaseSchema):
    username: str = Field(..., description="username")
    password: str = Field(..., description="password")


class UserCreateResp(BaseSchema):
    user_id: int = Field(..., description="user id")



class UserUpdate(BaseSchema):
    pass



class UserBase(BaseSchema):
    pass



class UserDelete(BaseSchema):
    pass


class UserFindByPage(BasePageSchema):
    pass



class UserFindById(BaseSchema):
    pass


