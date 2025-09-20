import traceback
from typing import Optional, Any
from fastapi import FastAPI, Request, status
from starlette.responses import JSONResponse
from fastapi.exceptions import HTTPException
from backend.common.errors import ErrorCode, BussinessCode
from backend.core.logs.loguru_config import Logger
from backend.common.resp_schema import ErrorResponse
from fastapi.exceptions import RequestValidationError
from pydantic_core import ValidationError as PydanticCoreValidationError


logx = Logger.get_logger()


class BusinessException(Exception):
    def __init__(
            self,
            message: str,
            code: int = BussinessCode.BUSSINESS_NORMAL_ERROR.code,
            status_code: int = ErrorCode.BAD_REQUEST,
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
            message=message,
            code=BussinessCode.VERIFY_PARAM_ERROR.code,
            status_code=ErrorCode.BAD_ENTITY,
            detail=detail
        )


# 权限异常
class ForbiddenException(BusinessException):
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            code=BussinessCode.FORBIDDEN_ERROR.code,
            status_code=ErrorCode.FORBIDDEN,
        )



# 认证异常
class AuthException(BusinessException):
    def __init__(self, message: str = "认证失败", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            code=BussinessCode.UNAUTHORIZED_ERROR.code,
            status_code=ErrorCode.UNAUTHORIZED,
            detail=detail
        )



class NotFoundException(BusinessException):
    def __init__(self, message: str = "资源未找到", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            code=BussinessCode.RESOURCE_NOT_FOUND_ERROR.code,
            status_code=ErrorCode.NOT_FOUND,
            detail=detail
        )


class ExceptionHandler:

    @staticmethod
    def add_exception_handlers(app: FastAPI) -> None:

        @app.exception_handler(BusinessException)
        async def business_exception_handler(request: Request, exc: BusinessException):
            request_id = getattr(request.state, "request_id", None)
            logx.bind(request_id=request_id).error(
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

        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            request_id = getattr(request.state, "request_id", None)
            errors = []
            for error in exc.errors():
                errors.append({
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                })

            logx.bind(request_id=request_id).error(
                f"RequestValidationError: {exc.errors()} "
                f"Request: {request.method} {request.url.path} "
            )
            response = ErrorResponse(
                code=BussinessCode.VERIFY_PARAM_ERROR.code,
                message="请求参数验证失败",
                detail=errors,
                request_id=request_id
            )
            return JSONResponse(
                status_code=ErrorCode.BAD_ENTITY,
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

            logx.bind(request_id=request_id).error(
                f"RequestValidationError: {exc.errors()} "
                f"Request: {request.method} {request.url.path} "
                f"Request ID: {request_id}"
            )
            response = ErrorResponse(
                code=BussinessCode.VERIFY_PARAM_ERROR.code,
                message=exc.message,
                detail=errors,
                request_id=request_id
            )
            return JSONResponse(
                status_code=ErrorCode.BAD_ENTITY,
                content=response.to_dict()
            )

        @app.exception_handler(ForbiddenException)
        async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
            request_id = getattr(request.state, "request_id", None)
            logx.bind(request_id=request_id).error(
                f"ForbiddenException: {exc.message} "
                f"(Code: {exc.code}, Status: {exc.status_code}) "
                f"Request: {request.method} {request.url.path} "
                f"Request ID: {request.state.request_id}"
            )
            return JSONResponse(
                code=exc.code,
                message=exc.message,
                data=exc.detail,
                request=request,
            )


        @app.exception_handler(HTTPException)
        async def not_found_exception_handler(request: Request, exc: HTTPException):
            request_id = getattr(request.state, "request_id", None)
            if exc.status_code == status.HTTP_404_NOT_FOUND:
                message = "请求的资源未找到"
            else:
                message = getattr(exc, "detail", "请求处理失败")

            logx.bind(request_id=request_id).error(
                f"HTTPException: {exc.status_code} - {message} "
                f"Request: {request.method} {request.url.path} "
                f"Request ID: {request_id}"
            )
            response = ErrorResponse(
                code=exc.status_code,
                message=message,
                detail=getattr(exc, 'header', None),
                request_id=request_id
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=response.to_dict()
            )

        @app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            request_id = getattr(request.state, "request_id", None)
            logx.bind(request_id=request_id).error(
                f"UnexpectedException: {str(exc)} "
                f"Type: {type(exc).__name__} "
                f"Request: {request.method} {request.url.path} "
                f"Request ID: {request_id}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            debug = getattr(request.app.state, "debug", False)
            detail = str(exc) if debug else None

            response = ErrorResponse(
                code=BussinessCode.BUSSINESS_NORMAL_ERROR.code,
                message="服务器内部错误",
                detail=detail,
                request_id=request_id
            )
            return JSONResponse(
                status_code=ErrorCode.INTERNAL_SERVER_ERROR,
                content=response.to_dict()
            )

        @app.exception_handler(PydanticCoreValidationError)
        async def pydantic_core_validation_error_handler(request: Request, exc: PydanticCoreValidationError):
            """
            处理 Pydantic Core ValidationError 异常
            """
            request_id = getattr(request.state, "request_id", None)
            errors = []
            for error in exc.errors():
                errors.append({
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                })

            logx.bind(request_id=request_id).error(
                f"PydanticCoreValidationError: {exc.errors()} "
                f"Request: {request.method} {request.url.path} "
                f"Request ID: {request_id}"
            )
            response = ErrorResponse(
                code=BussinessCode.VERIFY_PARAM_ERROR.code,
                message="数据验证失败",
                detail=errors,
                request_id=request_id
            )
            return JSONResponse(
                status_code=ErrorCode.BAD_ENTITY,
                content=response.to_dict()
            )

        @app.exception_handler(AuthException)
        async def auth_exception_handler(request: Request, exc: AuthException):
            request_id = getattr(request.state, "request_id", None)
            logx.bind(request_id=request_id).warning(
                f"AuthException: {exc.message} "
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

            # 添加WWW-Authenticate头
            headers = {"WWW-Authenticate": "Bearer"}
            return JSONResponse(
                status_code=exc.status_code,
                content=response.to_dict(),
                headers=headers
            )


def configure_exception_handlers(app: FastAPI):
    """设置异常处理器"""
    ExceptionHandler.add_exception_handlers(app)
    logx.info("Exception handlers registered successfully")
