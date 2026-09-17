from functools import wraps

import bcrypt
import jwt

from sanic import Blueprint
from sanic.response import json
from sanic_ext import openapi

from app.databases.mongodb import MongoDB
from app.decorators.auth import protected
from app.decorators.json_validator import validate_with_jsonschema
from app.hooks.error import ApiBadRequest, ApiForbidden, ApiInternalError, ApiNotFound, ApiUnauthorized
from app.utils.jwt_utils import decode_jwt, generate_token_pair


auth_bp = Blueprint('auth_blueprint', url_prefix='/auth')

_db = MongoDB()

USERNAME_SCHEMA = {'type': 'string', 'minLength': 1, 'maxLength': 64, 'pattern': r'\S'}
PASSWORD_SCHEMA = {'type': 'string', 'minLength': 1, 'maxLength': 72}
ROLE_SCHEMA = {'type': 'string', 'enum': ['admin', 'user']}

USER_BODY_PROPERTIES = {
	'username': USERNAME_SCHEMA,
	'password': PASSWORD_SCHEMA,
	'role': ROLE_SCHEMA,
}

credentials_json_schema = {
	'type': 'object',
	'additionalProperties': False,
	'properties': {
		'username': USERNAME_SCHEMA,
		'password': PASSWORD_SCHEMA,
	},
	'required': ['username', 'password']
}

admin_user_json_schema = {
	'type': 'object',
	'additionalProperties': False,
	'properties': USER_BODY_PROPERTIES,
	'required': ['username', 'password']
}

refresh_json_schema = {
	'type': 'object',
	'additionalProperties': False,
	'properties': {'refresh_token': {'type': 'string', 'minLength': 1}},
	'required': ['refresh_token'],
}

logout_json_schema = {
	'type': 'object',
	'additionalProperties': False,
	'properties': {'refresh_token': {'type': 'string', 'minLength': 1}},
}

update_user_json_schema = {
	'type': 'object',
	'additionalProperties': False,
	'properties': {
		'password': USER_BODY_PROPERTIES['password'],
		'role': USER_BODY_PROPERTIES['role'],
	},
	'minProperties': 1,
}


def _hash_password(password: str) -> str:
	return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _parse_user_role(body: dict) -> str:
	return body.get('role', 'user')


def _build_user_update(body: dict) -> dict:
	updated_data = {}
	if 'role' in body:
		updated_data['role'] = body['role']
	if 'password' in body:
		updated_data['password_hash'] = _hash_password(body['password'])
	return updated_data


@auth_bp.post('/register')
@openapi.tag('Authentication')
@openapi.summary('Register a user')
@openapi.description('Create a new user account')
@openapi.body({'application/json': credentials_json_schema})
@validate_with_jsonschema(jsonschema=credentials_json_schema)
async def register(request):
	username = request.json['username'].strip()
	password = request.json['password']

	if _db.get_user(username):
		raise ApiBadRequest('Username already exists')

	password_hash = _hash_password(password)
	user = _db.add_user(username, password_hash)
	if not user:
		raise ApiInternalError('Fail to create user')

	return json({'status': 'success', 'username': username}, status=201)


@auth_bp.post('/login')
@openapi.tag('Authentication')
@openapi.summary('Login')
@openapi.description('Authenticate a user and return access and refresh tokens')
@openapi.body({'application/json': credentials_json_schema})
@validate_with_jsonschema(jsonschema=credentials_json_schema)
async def login(request):
	username = request.json['username'].strip()
	password = request.json['password']
	user = _db.get_user(username)

	if not user or not bcrypt.checkpw(
		password.encode('utf-8'), user['password_hash'].encode('utf-8')
	):
		raise ApiUnauthorized('Invalid username or password')

	tokens = generate_token_pair(username, user.get('role', 'user'))
	return json({'status': 'success', 'token': tokens['access_token'], **tokens})


@auth_bp.post('/refresh')
@openapi.tag('Authentication')
@openapi.summary('Refresh tokens')
@openapi.description('Rotate the access and refresh tokens')
@openapi.body({'application/json': refresh_json_schema})
@validate_with_jsonschema(jsonschema=refresh_json_schema)
async def refresh(request):
	refresh_token = (request.json or {}).get('refresh_token')
	if not refresh_token:
		raise ApiUnauthorized('Refresh token is required')

	try:
		claims = decode_jwt(refresh_token)
		if claims.get('typ') != 'refresh' or await request.app.ctx.cache.is_jwt_revoked(claims['jti']):
			raise jwt.InvalidTokenError('Invalid or revoked refresh token')
	except (KeyError, jwt.InvalidTokenError):
		raise ApiUnauthorized('Invalid or expired refresh token')

	user = _db.get_user(claims['username'])
	if not user:
		raise ApiUnauthorized('Invalid or expired refresh token')

	await request.app.ctx.cache.revoke_jwt(claims['jti'], claims['exp'])
	tokens = generate_token_pair(user['username'], user.get('role', 'user'))
	return json({'status': 'success', 'token': tokens['access_token'], **tokens})


@auth_bp.post('/logout')
@openapi.tag('Authentication')
@openapi.summary('Logout')
@openapi.description('Revoke the current access token and optional refresh token')
@openapi.secured('BearerAuth')
@protected
async def logout(request, username=None, role=None):
	if request.json is not None and not isinstance(request.json, dict):
		raise ApiBadRequest('Request body must be a JSON object')
	if request.json and (
		set(request.json) - {'refresh_token'}
		or not isinstance(request.json.get('refresh_token'), str)
		or not request.json.get('refresh_token').strip()
	):
		raise ApiBadRequest('refresh_token must be a non-empty string')
	claims = decode_jwt(request.token)
	await request.app.ctx.cache.revoke_jwt(claims['jti'], claims['exp'])

	refresh_token = (request.json or {}).get('refresh_token')
	if refresh_token:
		try:
			refresh_claims = decode_jwt(refresh_token)
			if refresh_claims.get('typ') == 'refresh':
				await request.app.ctx.cache.revoke_jwt(refresh_claims['jti'], refresh_claims['exp'])
		except jwt.InvalidTokenError:
			pass

	return json({'status': 'success'})


def admin_only(handler):
	@wraps(handler)
	@protected
	async def admin_handler(request, username=None, role='user', **kwargs):
		if role != 'admin':
			raise ApiForbidden('Admin permission required')
		return await handler(request, username=username, role=role, **kwargs)

	return admin_handler


@auth_bp.get('/users')
@openapi.tag('Users')
@openapi.summary('Get users')
@openapi.description('Get all users')
@openapi.secured('BearerAuth')
@admin_only
async def get_users(request, username=None, role=None):
	users = _db.get_users()
	return json({'status': 'success', 'users': users})


@auth_bp.post('/users')
@openapi.tag('Users')
@openapi.summary('Create a user')
@openapi.description('Create a user account as an administrator')
@openapi.body({'application/json': admin_user_json_schema})
@openapi.secured('BearerAuth')
@admin_only
@validate_with_jsonschema(jsonschema=admin_user_json_schema)
async def create_user(request, username=None, role=None):
	body = request.json
	new_username = body['username'].strip()
	new_role = _parse_user_role(body)

	if _db.get_user(new_username):
		raise ApiBadRequest('Username already exists')

	if not _db.add_user(new_username, _hash_password(body['password']), new_role):
		raise ApiInternalError('Fail to create user')

	return json({'status': 'success', 'username': new_username}, status=201)


@auth_bp.put('/users/<target_username>')
@openapi.tag('Users')
@openapi.summary('Update a user')
@openapi.description('Update a user account as an administrator')
@openapi.body({'application/json': update_user_json_schema})
@openapi.secured('BearerAuth')
@admin_only
@validate_with_jsonschema(jsonschema=update_user_json_schema)
async def update_user(request, target_username, username=None, role=None):
	body = request.json
	updated_data = _build_user_update(body)

	if not _db.update_user(target_username, updated_data):
		raise ApiNotFound('User not found')

	return json({'status': 'success', 'username': target_username})


@auth_bp.delete('/users/<target_username>')
@openapi.tag('Users')
@openapi.summary('Delete a user')
@openapi.description('Delete a user account as an administrator')
@openapi.secured('BearerAuth')
@admin_only
async def delete_user(request, target_username, username=None, role=None):
	if username == target_username:
		raise ApiBadRequest('Admin cannot delete the current account')
	if not _db.delete_user(target_username):
		raise ApiBadRequest('User not found')

	return json({'status': 'success'})
