from typing import Any
from fastapi.encoders import jsonable_encoder
from pydantic import validate_call
from asgiref.sync import sync_to_async
from backend.common.errors import RequestCode, ResponseStatus

_excludeModel = set[int | str] | dict[int | str, Any]
__all__ = ['respBase']


class ResponseBase:

    @staticmethod
    @sync_to_async
    def _json_encoder(data: Any, exclude: _excludeModel | None = None, **kwargs):
        return jsonable_encoder(data, exclude=exclude, **kwargs)



    @validate_call
    async def success(
            self,
            data: Any = None,
            message: str = ResponseStatus.SUCCESS,
            code: int = RequestCode.SUCCESS,
            exclude: _excludeModel | None = None,
            **kwargs
    ):
        data = None if data is None else await self._json_encoder(data, exclude=exclude, **kwargs)
        return {
            "code": code,
            "message": message,
            "data": data
        }


    @validate_call
    async def fail(
            self,
            message: str = ResponseStatus.FAIL,
            code: int = RequestCode.INTERNAL_ERROR,
            data: Any = None,
            exclude: _excludeModel | None = None,
            **kwargs
    ) -> dict:
        data = None if data is None else await self._json_encoder(data, exclude=exclude, **kwargs)
        return {
            "code": code,
            "message": message,
            "data": data
        }


    @validate_call
    async def failWithCustomMessage(self, code: int, message: str, data: Any = None, exclude: _excludeModel | None = None,
                             **kwargs):
        data = None if data is None else await self._json_encoder(data, exclude=exclude, **kwargs)
        return {
            "code": code,
            "message": message,
            "data": data
        }


    @validate_call
    async def successWithCustomMessage(self, code: int, message: str, data: Any = None,
                                    exclude: _excludeModel | None = None,
                                    **kwargs):
        data = None if data is None else await self._json_encoder(data, exclude=exclude, **kwargs)
        return {
            "code": code,
            "message": message,
            "data": data
        }



    @validate_call
    async def failWithAuthorization(self, message: str = "Unauthorized") -> dict:
        return {
            "code": RequestCode.AUTHORIZATION_ERROR,
            "message": message,
            "data": None
        }

    @validate_call
    async def failWithNotFound(self, message: str = "Not Found"):
       return {
           "code": RequestCode.NOT_FOUND,
           "message": message,
           "data": None
       }


    @validate_call
    async def failBadRequest(self, message: str = "Bad Request"):
        return {
            "code": RequestCode.BAD_REQUEST,
            "message": message,
            "data": None
        }


    @validate_call
    async def failInternalError(self, message: str = ResponseStatus.ERROR):
        return {
            "code": RequestCode.INTERNAL_ERROR,
            "message": message,
            "data": None
        }



respBase = ResponseBase()
