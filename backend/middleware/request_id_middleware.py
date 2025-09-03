import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

class RequestIDMiddleware(BaseHTTPMiddleware):

    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Request-ID",
        force_new: bool = False
    ):
        super().__init__(app)
        self.header_name = header_name
        self.force_new = force_new

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取或生成request_id
        request_id = self._get_or_generate_request_id(request)
        request.state.request_id = request_id

        response = await call_next(request)

        # 在响应头中返回request_id
        response.headers[self.header_name] = request_id

        return response

    def _get_or_generate_request_id(self, request: Request) -> str:
        """获取或生成request_id"""
        request_id = None

        # 如果不强制生成新ID，尝试从请求头获取
        if not self.force_new:
            request_id = request.headers.get(self.header_name)

        # 如果没有获取到有效的request_id，则生成新的
        if not request_id:
            request_id = str(uuid.uuid4())

        return request_id
