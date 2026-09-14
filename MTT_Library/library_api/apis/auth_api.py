import json
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from library_api.databases.mongodb import MongoDB
from library_api.decorators.auth import require_jwt, require_role
from library_api.hooks.error import api_error
from library_api.security.password import hash_password, password_matches


def _body(request):
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return None


def _credentials(payload):
    if not isinstance(payload, dict):
        return False
    username = payload.get('username')
    password = payload.get('password')
    return (
        isinstance(username, str) and 3 <= len(username.strip()) <= 64
        and isinstance(password, str) and 8 <= len(password) <= 72
    )


def _encode(username, role, token_type, lifetime):
    now = datetime.now(timezone.utc)
    claims = {
        'sub': username,
        'username': username,
        'role': role,
        'typ': token_type,
        'jti': str(uuid.uuid4()),
        'iat': now,
        'exp': now + timedelta(seconds=lifetime),
    }
    token = jwt.encode(
        claims,
        settings.JWT_SECRET_KEYS[settings.JWT_ACTIVE_KID],
        algorithm='HS256',
        headers={'kid': settings.JWT_ACTIVE_KID},
    )
    return token, claims


def _decode(token):
    header = jwt.get_unverified_header(token)
    key = settings.JWT_SECRET_KEYS.get(header.get('kid'))
    if not key:
        raise jwt.InvalidTokenError('Unknown signing key')
    return jwt.decode(token, key, algorithms=['HS256'])


def _token_pair(username, role):
    access, access_claims = _encode(username, role, 'access', settings.JWT_ACCESS_EXPIRATION)
    refresh, refresh_claims = _encode(username, role, 'refresh', settings.JWT_REFRESH_EXPIRATION)
    return {
        'access_token': access,
        'refresh_token': refresh,
        'token_type': 'Bearer',
        'expires_in': settings.JWT_ACCESS_EXPIRATION,
        '_claims': (access_claims, refresh_claims),
    }


@require_http_methods(['POST'])
def register(request):
    payload = _body(request)
    if not _credentials(payload):
        return api_error('username must be 3-64 chars and password 8-72 chars', 400)
    username = payload['username'].strip()
    database = MongoDB()
    if database.get_user(username):
        return api_error('Username already exists', 400)
    if not database.create_user({
        'username': username,
        'password_hash': hash_password(payload['password']),
        'role': 'user',
    }):
        return api_error('Unable to create user', 500)
    return JsonResponse({'status': 'success', 'username': username}, status=201)


@require_http_methods(['POST'])
def login(request):
    payload = _body(request)
    if not _credentials(payload):
        return api_error('username must be 3-64 chars and password 8-72 chars', 400)
    user = MongoDB().get_user(payload['username'].strip())
    if not user or not password_matches(payload['password'], user['password_hash']):
        return api_error('Invalid username or password', 401)
    pair = _token_pair(user['username'], user.get('role', 'user'))
    pair.pop('_claims')
    return JsonResponse({'status': 'success', 'token': pair['access_token'], **pair})


@require_http_methods(['POST'])
def refresh(request):
    payload = _body(request) or {}
    try:
        claims = _decode(payload['refresh_token'])
        if claims.get('typ') != 'refresh' or MongoDB().is_token_revoked(claims.get('jti')):
            raise jwt.InvalidTokenError('Revoked refresh token')
    except (KeyError, jwt.InvalidTokenError):
        return api_error('Invalid or revoked refresh token', 401)
    pair = _token_pair(claims['username'], claims.get('role', 'user'))
    MongoDB().revoke_token(claims['jti'], datetime.fromtimestamp(claims['exp'], timezone.utc))
    pair.pop('_claims')
    return JsonResponse({'status': 'success', 'token': pair['access_token'], **pair})


@require_jwt
@require_http_methods(['POST'])
def logout(request):
    claims = request.user_claims
    database = MongoDB()
    database.revoke_token(claims['jti'], datetime.fromtimestamp(claims['exp'], timezone.utc))
    refresh_token = (_body(request) or {}).get('refresh_token')
    if refresh_token:
        try:
            refresh_claims = _decode(refresh_token)
            if refresh_claims.get('typ') == 'refresh':
                database.revoke_token(
                    refresh_claims['jti'],
                    datetime.fromtimestamp(refresh_claims['exp'], timezone.utc),
                )
        except jwt.InvalidTokenError:
            pass
    return JsonResponse({'status': 'success', 'message': 'Token revoked'})


@require_role('admin')
@require_http_methods(['GET'])
def list_users(request):
    return JsonResponse({'status': 'success', 'users': MongoDB().list_users()})


@require_role('admin')
@require_http_methods(['POST'])
def create_user(request):
    payload = _body(request)
    if not _credentials(payload) or payload.get('role', 'user') not in ('admin', 'user'):
        return api_error('Invalid user payload', 400)
    username = payload['username'].strip()
    database = MongoDB()
    if database.get_user(username):
        return api_error('Username already exists', 400)
    if not database.create_user({
        'username': username,
        'password_hash': hash_password(payload['password']),
        'role': payload.get('role', 'user'),
    }):
        return api_error('Unable to create user', 500)
    return JsonResponse({'status': 'success', 'username': username}, status=201)


@require_role('admin')
@require_http_methods(['PUT', 'DELETE'])
def manage_user(request, username):
    database = MongoDB()
    if request.method == 'DELETE':
        if request.user_claims['username'] == username:
            return api_error('Admin cannot delete the current account', 400)
        if not database.delete_user(username):
            return api_error('User not found', 404)
        return JsonResponse({'status': 'success'})
    payload = _body(request) or {}
    updates = {}
    if payload.get('role') in ('admin', 'user'):
        updates['role'] = payload['role']
    if isinstance(payload.get('password'), str) and 8 <= len(payload['password']) <= 72:
        updates['password_hash'] = hash_password(payload['password'])
    if not updates or not database.update_user(username, updates):
        return api_error('No valid user update was provided', 400)
    return JsonResponse({'status': 'success', 'username': username})
