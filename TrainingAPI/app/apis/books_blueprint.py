import re
from urllib.parse import quote_plus

from sanic import Blueprint
from sanic.response import json
from sanic_ext import openapi

from app.constants.cache_constants import CacheConstants
from app.databases.mongodb import MongoDB
from app.databases.redis_cached import RedisCache
from app.decorators.auth import protected
from app.decorators.json_validator import validate_with_jsonschema
from app.hooks.error import ApiBadRequest, ApiForbidden, ApiNotFound, ApiInternalError
from app.models.book import create_book_json_schema, Book
from app.utils.datetime_utils import utc_now_iso

books_bp = Blueprint('books_blueprint', url_prefix='/books')

_db = MongoDB()


@books_bp.get('/')
# Config swagger example
@openapi.tag('Books')
@openapi.summary('Get all books')
@openapi.description('Get all books from database')
# -----
async def get_all_books(request):
    cache: RedisCache = request.app.ctx.cache
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
    except ValueError:
        raise ApiBadRequest('page and per_page must be integers')
    if page < 1 or not 1 <= per_page <= 100:
        raise ApiBadRequest('page must be >= 1 and per_page must be between 1 and 100')

    filters = {}
    for key in ('title', 'publisher', 'owner'):
        value = request.args.get(key)
        if value:
            filters[key] = {'$regex': re.escape(value), '$options': 'i'}
    author = request.args.get('author')
    if author:
        filters['authors'] = {'$regex': re.escape(author), '$options': 'i'}
    cache_key = CacheConstants.books_key(page, per_page, {
        key: quote_plus(str(value), safe='') for key, value in filters.items()
    })
    try:
        result = await cache.get(cache_key)
    except Exception:
        result = None

    if result is None:
        books, total = _db.get_books_page(page, per_page, filters)
        result = {'books': books, 'total': total, 'page': page, 'per_page': per_page}
        try:
            await cache.set(cache_key, result)
        except Exception:
            pass
    return json({'status': 'success', **result})


@books_bp.post('/')
# Config swagger example
@openapi.tag('Books')
@openapi.summary('Create a book')
@openapi.description('Create a book in database')
@openapi.body({'application/json': create_book_json_schema})
# -----
# Middleware for validate JWT
@openapi.secured('BearerAuth')
@protected
# -----
# Validate data from request
@validate_with_jsonschema(jsonschema=create_book_json_schema)
# -----
async def create_book(request, username=None, role='user'):
    body = request.json

    id = _db.get_next_book_id()
    book = Book(id).from_dict(body)
    now = utc_now_iso()
    book.created_at = now
    book.last_updated_at = now
    book.owner = username

    inserted = _db.add_book(book)
    if not inserted:
        raise ApiInternalError('Fail to create book')
    
    cache: RedisCache = request.app.ctx.cache
    try:
        await cache.invalidate_books()
    except Exception:
        pass

    return json({
        'status': 'success',
        'book': book.to_dict()
    }, status=201)

@books_bp.get('/<id>')
@openapi.tag('Books')
@openapi.summary('Get a book')
@openapi.description('Get a book by id in database')
async def get_book_by_id(request, id):
    cache: RedisCache = request.app.ctx.cache
    cache_key = f'book:{id}'

    try:
        book_data = await cache.get(cache_key)
    except Exception:
        book_data = None

    if book_data is None:
        book = _db.get_book_by_id(id)
        if not book:
            raise ApiNotFound('Book not found')

        book_data = book.to_dict()
        try:
            await cache.set(cache_key, book_data)
        except Exception:
            pass

    return json({'status': 'success', 'book': book_data})

@books_bp.put('/<id>')
@openapi.tag('Books')
@openapi.summary('Update a book')
@openapi.description('Update a book by id in database')
@openapi.body({'application/json': create_book_json_schema})
@openapi.secured('BearerAuth')
@protected
@validate_with_jsonschema(jsonschema=create_book_json_schema)
async def update_book(request, id, username, role='user'):
    body = request.json
    book = _db.get_book_by_id(id)
    now = utc_now_iso()
    if not book:
        raise ApiNotFound('Book not found')
    
    if role != 'admin' and book.owner != username:
        raise ApiForbidden('Forbidden to update this book')

    newbook = Book(id).from_dict(body)
    book.title = newbook.title
    book.authors = newbook.authors
    book.publisher = newbook.publisher
    book.description = newbook.description
    book.last_updated_at = now

    if not _db.update_book(id, book.to_dict()):
        raise ApiInternalError('Fail to update book')

    cache: RedisCache = request.app.ctx.cache
    try:
        await cache.invalidate_books()
        await cache.delete(f'book:{id}')
    except Exception:
        pass

    return json({'status': 'success', 'book': book.to_dict()})

@books_bp.delete('/<id>')
@openapi.tag('Books')
@openapi.summary('Delete a book')
@openapi.description('Delete a book by id from database')
@openapi.secured('BearerAuth')
@protected
async def delete_book(request, id, username, role='user'):
    book = _db.get_book_by_id(id)
    if not book:
        raise ApiNotFound('Book not found')

    if role != 'admin' and book.owner != username:
        raise ApiForbidden('Unauthorized to delete this book')

    deleted = _db.delete_book(id)
        
    if not deleted:
        raise ApiInternalError('Fail to delete book')
    
    cache: RedisCache = request.app.ctx.cache
    try:
        await cache.invalidate_books()
        await cache.delete(f'book:{id}')
    except Exception:
        pass

    return json({'status': 'success'})

