import json
from typing import Any
from fastapi import Request





class MessageUtils:



    @staticmethod
    def get_client_ip(request: Request) -> str:
        # 处理反向代理情况（如Nginx、Traefik等）
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # X-Forwarded-For可能包含多个IP，取第一个
            return x_forwarded_for.split(",")[0].strip()

        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip

        if request.client:
            return request.client.host

        return None


    @staticmethod
    def json_format(jsonstr: str) -> Any:
        return json.loads(jsonstr)


