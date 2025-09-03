from typing import Optional, Any

from pydantic import BaseModel
from datetime import datetime

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }




class BasePageSchema(BaseSchema):
    page: int = 1
    page_size: int = 10



class BasePageResponse(BaseSchema):
    total: int
    data: Any


