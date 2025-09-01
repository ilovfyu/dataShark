import traceback
from typing import Optional, Any
from fastapi import FastAPI, Request, status
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from backend.common.errors import ErrorCode
from backend.core.logs.loguru_config import Logger
from backend.common.resp_schema import ResponseUtil, ErrorResponse

logger = Logger.get_logger()



class BusinessException(Exception):
    def __init__(
            self,
            message: str,
            code: int = ErrorCode.BAD_REQUEST,
            status_code: int = status.HTTP_400_BAD_REQUEST,
            detail: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)





class ValidationException(BusinessException):
    def __init__(self, message: str = "数据验证失败", detail: Optional[Any] = None):
        super().__init__(
            message = message,
            code = ErrorCode.VALIDATION_ERROR,
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = detail
        )



# 权限异常
class ForbiddenException(BusinessException):
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            code=ErrorCode.FORBIDDEN,
            status_code=status.HTTP_403_FORBIDDEN
        )



class ExceptionHandler:


    @staticmethod
    def add_exception_handlers(app: FastAPI) -> None:



        @app.exception_handler(BusinessException)
        async def business_exception_handler(request: Request, exc: BusinessException):
            request_id = getattr(request.state, "request_id", None)
            logger.warning(
                f"BusinessException: {exc.message} "
                f"(Code: {exc.code}, Status: {exc.status_code}) "
                f"Request: {request.method} {request.url.path} "
                f"Request ID: {request_id}"
            )
            response = ErrorResponse(
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
                request_id=request_id
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=response.to_dict()
            )


        @app.exception_handler(ValidationException)
        async def validation_exception_handler(request: Request, exc: ValidationException):
            request_id = getattr(request.state, "request_id", None)
            errors = []
            for error in exc.errors():
                errors.append({
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                })

            logger.warning(
                f"RequestValidationError: {exc.errors()} "
                f"Request: {request.method} {request.url.path} "
                f"Request ID: {request_id}"
            )
            response = ErrorResponse(
                code=ErrorCode.VALIDATION_ERROR,
                message="请求参数验证失败",
                detail=errors,
                request_id=request_id
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=response.to_dict()
            )



        @app.exception_handler(ForbiddenException)
        async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
            logger.warning(
                f"ForbiddenException: {exc.message} "
                f"(Code: {exc.code}, Status: {exc.status_code}) "
                f"Request: {request.method} {request.url.path} "
                f"Request ID: {request.state.request_id}"
            )
            return ResponseUtil.json_response(
                code=exc.code,
                message=exc.message,
                data=exc.detail,
                request=request,
            )



        @app.exception_handler(StarletteHTTPException)
        async def not_found_exception_handler(request: Request, exc: StarletteHTTPException):
            request_id = getattr(request.state, "request_id", None)
            if exc.status_code == status.HTTP_404_NOT_FOUND:
                message = "请求的资源未找到"
            else:
                message = getattr(exc, 'detail', '请求处理失败')

            logger.warning(
                f"HTTPException: {exc.status_code} - {message} "
                f"Request: {request.method} {request.url.path} "
                f"Request ID: {request_id}"
            )
            response = ErrorResponse(
                code=exc.status_code,
                message=message,
                detail=getattr(exc, 'detail', None),
                request_id=request_id
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=response.to_dict()
            )


        @app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            request_id = getattr(request.state, "request_id", None)

            logger.error(
                f"UnexpectedException: {str(exc)} "
                f"Type: {type(exc).__name__} "
                f"Request: {request.method} {request.url.path} "
                f"Request ID: {request_id}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            debug = getattr(request.app.state, "debug", False)
            detail = str(exc) if debug else None

            response = ErrorResponse(
                code=ErrorCode.INTERNAL_ERROR,
                message="服务器内部错误",
                detail=detail,
                request_id=request_id
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=response.to_dict()
            )


def configure_exception_handlers(app: FastAPI):
    """设置异常处理器"""
    ExceptionHandler.add_exception_handlers(app)
    logger.info("Exception handlers registered successfully")