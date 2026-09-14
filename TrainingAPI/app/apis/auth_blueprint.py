import bcrypt

from sanic import Blueprint
from sanic.response import json

from app.databases.mongodb import MongoDB
from app.decorators.auth import protected
from app.decorators.json_validator import validate_with_jsonschema
from app.hooks.error import ApiBadRequest, ApiForbidden, ApiInternalError, ApiUnauthorized
from app.utils.jwt_utils import generate_jwt


auth_bp = Blueprint('auth_blueprint', url_prefix='/auth')

_db = MongoDB()

credentials_json_schema = {
	'type': 'object',
	'additionalProperties': False,
	'properties': {
		'username': {'type': 'string', 'minLength': 3, 'maxLength': 64},
		'password': {'type': 'string', 'minLength': 8, 'maxLength': 72},
	},
	'required': ['username', 'password']
}

admin_user_json_schema = {
	'type': 'object',
	'additionalProperties': False,
	'properties': {
		'username': {'type': 'string', 'minLength': 3, 'maxLength': 64},
		'password': {'type': 'string', 'minLength': 8, 'maxLength': 72},
		'role': {'type': 'string', 'enum': ['admin', 'user']},
	},
	'required': ['username', 'password']
}


@auth_bp.post('/register')
@validate_with_jsonschema(jsonschema=credentials_json_schema)
async def register(request):
	username = request.json['username'].strip()
	password = request.json['password']

	if not username:
		raise ApiBadRequest('Username must not be empty')

	if _db.get_user(username):
		raise ApiBadRequest('Username already exists')

	password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
	user = _db.add_user(username, password_hash)
	if not user:
		raise ApiInternalError('Fail to create user')

	return json({'status': 'success', 'username': username}, status=201)


@auth_bp.post('/login')
@validate_with_jsonschema(jsonschema=credentials_json_schema)
async def login(request):
	username = request.json['username'].strip()
	password = request.json['password']
	user = _db.get_user(username)

	if not user or not bcrypt.checkpw(
		password.encode('utf-8'), user['password_hash'].encode('utf-8')
	):
		raise ApiUnauthorized('Invalid username or password')

	token = generate_jwt(username, user.get('role', 'user'))
	return json({'status': 'success', 'token': token, 'token_type': 'Bearer'})


def admin_only(handler):
	@protected
	async def admin_handler(request, username=None, role='user', **kwargs):
		if role != 'admin':
			raise ApiForbidden('Admin permission required')
		return await handler(request, username=username, role=role, **kwargs)

	return admin_handler


@auth_bp.get('/users')
@admin_only
async def get_users(request, username=None, role=None):
	users = _db.get_users()
	return json({'status': 'success', 'users': users})


@auth_bp.post('/users')
@admin_only
@validate_with_jsonschema(jsonschema=admin_user_json_schema)
async def create_user(request, username=None, role=None):
	new_username = request.json['username'].strip()
	password = request.json['password']
	new_role = request.json.get('role', 'user')

	if not new_username:
		raise ApiBadRequest('Username must not be empty')
	if _db.get_user(new_username):
		raise ApiBadRequest('Username already exists')

	password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
	if not _db.add_user(new_username, password_hash, new_role):
		raise ApiInternalError('Fail to create user')

	return json({'status': 'success', 'username': new_username}, status=201)


@auth_bp.put('/users/<target_username>')
@admin_only
async def update_user(request, target_username, username=None, role=None):
	body = request.json or {}
	updated_data = {}

	if 'role' in body:
		if body['role'] not in ('admin', 'user'):
			raise ApiBadRequest('Role must be admin or user')
		updated_data['role'] = body['role']
	if 'password' in body:
		password = body['password']
		if not isinstance(password, str) or not 8 <= len(password) <= 72:
			raise ApiBadRequest('Password must contain 8 to 72 characters')
		updated_data['password_hash'] = bcrypt.hashpw(
			password.encode('utf-8'), bcrypt.gensalt()
		).decode('utf-8')

	if not updated_data or not _db.update_user(target_username, updated_data):
		raise ApiBadRequest('No valid user update was provided')

	return json({'status': 'success', 'username': target_username})


@auth_bp.delete('/users/<target_username>')
@admin_only
async def delete_user(request, target_username, username=None, role=None):
	if username == target_username:
		raise ApiBadRequest('Admin cannot delete the current account')
	if not _db.delete_user(target_username):
		raise ApiBadRequest('User not found')

	return json({'status': 'success'})
