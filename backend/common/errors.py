from enum import Enum, IntEnum, unique



@unique
class ResponseStatus(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
    ERROR = "error"




@unique
class RequestCode(IntEnum):
    # 2xx
    SUCCESS = 200
    CREATED = 201
    ACCEPTED = 202

    # 4xx
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    VALIDATION_ERROR = 422

    # 5xx
    INTERNAL_ERROR = 500
    NOT_IMPLEMENTED = 501
    SERVICE_UNAVAILABLE = 503


@unique
class BusinessCode(IntEnum):
    USER_NOT_FOUND = 10001
    INVALID_CREDENTIALS = 10002
    INSUFFICIENT_PERMISSIONS = 10003