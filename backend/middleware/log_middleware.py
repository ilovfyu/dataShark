import time
import uuid
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from backend.core.logs.loguru_config import Logger

logger = Logger.get_logger()

class LoguruMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        skip_routes: Optional[list] = None,
        skip_keywords: Optional[list] = None
    ):
        super().__init__(app)
        self.skip_routes = skip_routes or []
        self.skip_keywords = skip_keywords or []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否需要跳过日志记录
        if self._should_skip_log(request):
            return await call_next(request)

        # 从request.state获取request_id
        request_id = getattr(request.state, "request_id", self._generate_fallback_id())
        # 记录请求开始时间
        start_time = time.time()

        # 记录请求信息
        await self._log_request(request, request_id)

        try:
            # 处理请求
            response = await call_next(request)

            # 记录响应信息
            process_time = time.time() - start_time
            await self._log_response(request, response, process_time, request_id)

            return response

        except Exception as e:
            # 记录异常信息
            process_time = time.time() - start_time
            await self._log_exception(request, e, process_time, request_id)
            raise

    def _should_skip_log(self, request: Request) -> bool:
        """判断是否应该跳过日志记录"""
        path = request.url.path

        # 检查是否在跳过路由中
        for route in self.skip_routes:
            if path.startswith(route):
                return True

        # 检查是否包含跳过关键词
        for keyword in self.skip_keywords:
            if keyword in path:
                return True

        return False

    async def _log_request(self, request: Request, request_id: str):
        """记录请求信息"""
        try:
            # 获取请求体（仅对小请求体进行记录）
            body = None
            if hasattr(request, "_body"):
                body = await request.body()
            elif request.method in ["POST", "PUT", "PATCH"]:
                # 读取请求体会消耗流，需要特殊处理
                pass

            logger.info(
                f"[{request_id}] Request: {request.method} {request.url.path} "
                f"Client: {request.client.host}:{request.client.port} "
                f"Headers: {dict(request.headers)}"
            )

        except Exception as e:
            logger.warning(f"[{request_id}] Failed to log request body: {e}")

    async def _log_response(self, request: Request, response: Response, process_time: float, request_id: str):
        """记录响应信息"""
        try:
            status_code = response.status_code
            content_length = response.headers.get("content-length", "unknown")

            # 根据状态码确定日志级别
            if 200 <= status_code < 300:
                log_method = logger.info
            elif 400 <= status_code < 500:
                log_method = logger.warning
            else:
                log_method = logger.error

            log_method(
                f"[{request_id}] Response: {request.method} {request.url.path} "
                f"Status: {status_code} Duration: {process_time:.3f}s "
                f"Content-Length: {content_length}"
            )

        except Exception as e:
            logger.warning(f"[{request_id}] Failed to log response: {e}")

    async def _log_exception(self, request: Request, exception: Exception, process_time: float, request_id: str):
        """记录异常信息"""
        logger.error(
            f"[{request_id}] Exception: {request.method} {request.url.path} "
            f"Error: {str(exception)} Duration: {process_time:.3f}s"
        )

    def _generate_fallback_id(self) -> str:
        """生成备用request_id"""
        return str(uuid.uuid4())
