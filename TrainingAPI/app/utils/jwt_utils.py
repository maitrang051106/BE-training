import datetime
import uuid

import jwt

from config import Config


def generate_jwt(username, role='user', token_type='access', lifetime=None):
    lifetime = lifetime or Config.JWT_ACCESS_EXPIRATION
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    expiration_time = now + datetime.timedelta(seconds=lifetime)
    token = jwt.encode(
        {
            "username": username,
            "role": role,
            "typ": token_type,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": expiration_time
        },
        Config.SECRET_KEY,
        algorithm='HS256'
    )

    return token


def generate_token_pair(username, role='user'):
    return {
        'access_token': generate_jwt(username, role, 'access', Config.JWT_ACCESS_EXPIRATION),
        'refresh_token': generate_jwt(username, role, 'refresh', Config.JWT_REFRESH_EXPIRATION),
        'token_type': 'Bearer',
        'expires_in': Config.JWT_ACCESS_EXPIRATION,
    }


def decode_jwt(token):
    return jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
