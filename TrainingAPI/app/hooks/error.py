from sanic.exceptions import SanicException
from sanic.response import json


class _ApiError(SanicException):
    def __init__(self, message, status_code=None, quiet=None):
        super().__init__(message=message, status_code=status_code, quiet=quiet)


class ApiBadRequest(_ApiError):
    def __init__(self, message, quiet=None):
        status_code = 400
        message = 'Bad Request: ' + message
        super().__init__(message=message, status_code=status_code, quiet=quiet)


class ApiUnauthorized(_ApiError):
    def __init__(self, message, quiet=None):
        status_code = 401
        message = 'Unauthorized: ' + message
        super().__init__(message=message, status_code=status_code, quiet=quiet)


class ApiForbidden(_ApiError):
    def __init__(self, message, quiet=None):
        status_code = 403
        message = 'Forbidden: ' + message
        super().__init__(message=message, status_code=status_code, quiet=quiet)


class ApiNotFound(_ApiError):
    def __init__(self, message, quiet=None):
        status_code = 404
        message = 'Not Found: ' + message
        super().__init__(message=message, status_code=status_code, quiet=quiet)


class ApiInternalError(_ApiError):
    def __init__(self, message, quiet=None):
        status_code = 500
        message = 'Internal Error: ' + message
        super().__init__(message=message, status_code=status_code, quiet=quiet)


class ApiDatabaseError(_ApiError):
    def __init__(self, message='Database operation failed', quiet=None):
        super().__init__(message=message, status_code=503, quiet=quiet)


async def api_error_handler(request, exception):
    return json({
        'status': 'error',
        'error': {
            'code': exception.status_code,
            'message': str(exception),
        },
    }, status=exception.status_code)
