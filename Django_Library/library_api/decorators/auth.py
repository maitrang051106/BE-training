from functools import wraps

import jwt
from django.conf import settings

from library_api.databases.mongodb import MongoDB
from library_api.hooks.error import api_error


def require_jwt(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        header = request.headers.get('Authorization', '')
        scheme, _, token = header.partition(' ')
        if scheme.lower() != 'bearer' or not token:
            return api_error('Bearer token is required', 401)
        try:
            header = jwt.get_unverified_header(token)
            key = settings.JWT_SECRET_KEYS.get(header.get('kid'))
            if not key:
                return api_error('Unknown signing key', 401)
            claims = jwt.decode(token, key, algorithms=['HS256'])
            if claims.get('typ') != 'access' or MongoDB().is_token_revoked(claims.get('jti')):
                return api_error('Token has been revoked or is not an access token', 401)
            request.user_claims = claims
        except jwt.InvalidTokenError:
            return api_error('Invalid or expired token', 401)
        return view(request, *args, **kwargs)

    return wrapped


def require_role(role):
    def decorator(view):
        @wraps(view)
        @require_jwt
        def wrapped(request, *args, **kwargs):
            if request.user_claims.get('role') != role:
                return api_error('Permission denied', 403)
            return view(request, *args, **kwargs)

        return wrapped

    return decorator