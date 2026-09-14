import time
import uuid

from sanic import Blueprint
from sanic.response import json
from sanic_ext import openapi

from app.constants.cache_constants import CacheConstants
from app.databases.mongodb import MongoDB
from app.databases.redis_cached import RedisCache
from app.decorators.auth import protected
from app.decorators.json_validator import validate_with_jsonschema
from app.hooks.error import ApiForbidden, ApiNotFound, ApiInternalError
from app.models.book import create_book_json_schema, Book

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
        books = await cache.get(CacheConstants.all_books)
    except Exception:
        books = None

    if books is None:
        book_objs = _db.get_books()
        books = [book.to_dict() for book in book_objs]
        await cache.set(CacheConstants.all_books, books)
    number_of_books = len(books)
    return json({
        'n_books': number_of_books,
        'books': books
    })


@books_bp.post('/')
# Config swagger example
@openapi.tag('Books')
@openapi.summary('Create a book')
@openapi.description('Create a book in database')
@openapi.body({'application/json': create_book_json_schema})
# -----
# Middleware for validate JWT
@protected
# -----
# Validate data from request
@validate_with_jsonschema(jsonschema=create_book_json_schema)
# -----
async def create_book(request, username=None):
    body = request.json

    id = str(uuid.uuid4())
    book = Book(id).from_dict(body)
    now = int(time.time())
    book.created_at = now
    book.last_updated_at = now
    book.owner = username

    inserted = _db.add_book(book)
    if not inserted:
        raise ApiInternalError('Fail to create book')
    
    cache: RedisCache = request.app.ctx.cache
    await cache.delete(CacheConstants.all_books)

    return json({
        'status': '201',
        'book': book.to_dict()
    })

@books_bp.get('/<id>')
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
@protected
@validate_with_jsonschema(jsonschema=create_book_json_schema)
async def update_book(request, id, username, role='user'):
    body = request.json
    book = _db.get_book_by_id(id)
    now = int(time.time())
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
    await cache.delete(CacheConstants.all_books)
    await cache.delete(f'book:{id}')

    return json({'status': 'success', 'book': book.to_dict()})

@books_bp.delete('/<id>')
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
    await cache.delete(CacheConstants.all_books)
    await cache.delete(f'book:{id}')

    return json({'status': 'success'})

