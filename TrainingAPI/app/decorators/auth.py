from functools import wraps
import jwt

from app.hooks.error import ApiUnauthorized
from app.utils.jwt_utils import decode_jwt


async def check_token(request):
    token = request.token
    if not token:
        return False, None

    try:
        jwt_ = decode_jwt(token)
        if jwt_.get('typ') != 'access' or await request.app.ctx.cache.is_jwt_revoked(jwt_['jti']):
            return False, None
        return True, jwt_
    except jwt.exceptions.InvalidTokenError:
        return False, None


def protected(wrapped):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            is_authenticated, jwt_ = await check_token(request)

            if is_authenticated:
                kwargs['username'] = jwt_['username']
                kwargs['role'] = jwt_.get('role', 'user')
                response = await f(request, *args, **kwargs)
                return response
            else:
                raise ApiUnauthorized("You are unauthorized.")

        return decorated_function

    return decorator(wrapped)
