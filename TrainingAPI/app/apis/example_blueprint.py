from sanic import Blueprint
from sanic.response import json
from sanic_ext import openapi

example = Blueprint('example_blueprint', url_prefix='')


@example.route('/')
@openapi.tag('Example')
@openapi.summary('List API endpoints')
@openapi.description('List available API endpoints, HTTP methods, and required permissions')
async def bp_root(request):
    return json({
        'status': 'success',
        'apis': [
            {'method': 'GET', 'path': '/v1', 'permission': 'public', 'description': 'List API endpoints'},
            {'method': 'POST', 'path': '/v1/auth/register', 'permission': 'public', 'description': 'Register a user'},
            {'method': 'POST', 'path': '/v1/auth/login', 'permission': 'public', 'description': 'Login'},
            {'method': 'POST', 'path': '/v1/auth/refresh', 'permission': 'public', 'description': 'Refresh tokens'},
            {'method': 'POST', 'path': '/v1/auth/logout', 'permission': 'authenticated', 'description': 'Logout'},
            {'method': 'GET', 'path': '/v1/auth/users', 'permission': 'admin', 'description': 'Get users'},
            {'method': 'POST', 'path': '/v1/auth/users', 'permission': 'admin', 'description': 'Create a user'},
            {'method': 'PUT', 'path': '/v1/auth/users/<target_username>', 'permission': 'admin', 'description': 'Update a user'},
            {'method': 'DELETE', 'path': '/v1/auth/users/<target_username>', 'permission': 'admin', 'description': 'Delete a user'},
            {'method': 'GET', 'path': '/v1/books', 'permission': 'public', 'description': 'Get all books'},
            {'method': 'POST', 'path': '/v1/books', 'permission': 'authenticated', 'description': 'Create a book'},
            {'method': 'GET', 'path': '/v1/books/<id>', 'permission': 'public', 'description': 'Get a book'},
            {'method': 'PUT', 'path': '/v1/books/<id>', 'permission': 'authenticated', 'description': 'Update a book'},
            {'method': 'DELETE', 'path': '/v1/books/<id>', 'permission': 'authenticated', 'description': 'Delete a book'},
        ],
    })
