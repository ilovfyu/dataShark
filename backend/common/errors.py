from enum import IntEnum



class ErrorCode(IntEnum):

    SUCCESS = 200
    CREATED = 201
    ACCEPTED = 202


    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    VALIDATION_ERROR = 422


    INTERNAL_ERROR = 500
    NOT_IMPLEMENTED = 501
    SERVICE_UNAVAILABLE = 503



class BussinessCode(IntEnum):

    pass