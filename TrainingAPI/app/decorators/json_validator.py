from functools import wraps

from jsonschema import ValidationError, validate
from sanic.request import Request

from app.hooks.error import ApiBadRequest


def validate_with_jsonschema(jsonschema: dict):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            for arg in args:
                if isinstance(arg, Request):
                    request: Request = arg

                    try:
                        if not isinstance(request.json, dict) or not request.json:
                            raise ApiBadRequest('Request body must be a non-empty JSON object')
                        validate(request.json, jsonschema)
                    except ValidationError as ex:
                        raise ApiBadRequest(ex.message)

            return await fn(*args, **kwargs)
        return wrapper
    return decorator
