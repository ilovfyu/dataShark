from typing import Any, Optional, Generic, TypeVar, Dict
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from enum import Enum

T = TypeVar('T')

class ResponseStatus(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
    ERROR = "error"

class UnifiedResponse(BaseModel, Generic[T]):
    code: int
    status: ResponseStatus
    message: Optional[str] = None
    data: Optional[T] = None
    request_id: Optional[str] = None
    timestamp: Optional[str] = None




class RespCall:

    @staticmethod
    def success(
        data: Any = None,
        code: int = 200,
        request: Request = None,
    ) -> dict:
        from datetime import datetime
        request_id = None
        if request:
            request_id = getattr(request.state, 'request_id', None)
        response = UnifiedResponse(
            code=code,
            status=ResponseStatus.SUCCESS,
            data=data,
            request_id=request_id,
            timestamp=datetime.now().isoformat()
        )
        return response.model_dump()

    @staticmethod
    def fail(
        message: str = "Operation failed",
        code: int = 400,
        data: Any = None,
        request: Request = None
    ) -> dict:
        from datetime import datetime
        request_id = None
        if request:
            request_id = getattr(request.state, 'request_id', None)
        response = UnifiedResponse(
            code=code,
            status=ResponseStatus.FAIL,
            message=message,
            data=data,
            request_id=request_id,
            timestamp=datetime.now().isoformat()
        )
        return response.model_dump()

    @staticmethod
    def error(
        message: str = "Internal server error",
        code: int = 500,
        data: Any = None,
        request: Request = None
    ) -> dict:
        from datetime import datetime

        request_id = None
        if request:
            request_id = getattr(request.state, 'request_id', None)

        response = UnifiedResponse(
            code=code,
            status=ResponseStatus.ERROR,
            message=message,
            data=data,
            request_id=request_id,
            timestamp=datetime.now().isoformat()
        )
        return response.model_dump()




class ErrorResponse:
    def __init__(
            self,
            code: int,
            message: str,
            detail: Optional[Any] = None,
            request_id: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.detail = detail
        self.request_id = request_id
    def to_dict(self) -> Dict[str, Any]:
        from datetime import datetime
        result = {
            "code": self.code,
            "message": self.message,
            "success": False,
            "timestamp": datetime.now().isoformat()
        }
        if self.detail is not None:
            result["detail"] = self.detail

        if self.request_id:
            result["request_id"] = self.request_id
        return result
