from typing import Optional, Any

from pydantic import BaseModel, Field
from datetime import datetime

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }




class BasePageReq(BaseSchema):
    page: int = 1
    page_size: int = 10



class BasePageResp(BaseSchema):
    total: int
    data: Any



class NoneDataUnionResp(BaseSchema):
    pong: str = Field(default="OK", description="union response if not exist data.")



