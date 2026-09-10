import uuid

from sanic import Blueprint
from sanic.response import json
from sanic_ext import openapi, validate

from app.constants.cache_constants import CacheConstants
from app.databases.mongodb import MongoDB
from app.databases.redis_cached import RedisCache
from app.decorators.auth import protected
from app.decorators.json_validator import validate_with_jsonschema
from app.hooks.error import ApiInternalError
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
    # # TODO: use cache to optimize api
    # cache: RedisCache = request.app.ctx.cache
    # books = await cache.get(CacheConstants.all_books)
    # if books is None:
    #     book_objs = _db.get_books()
    #     books = [book.to_dict() for book in book_objs]
    #     await cache.set(CacheConstants.all_books, books)

    book_objs = _db.get_books()
    books = [book.to_dict() for book in book_objs]
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
# @protected  # TODO: Authenticate
# -----
# Validate data from request
@validate_with_jsonschema(jsonschema=create_book_json_schema)
# -----
async def create_book(request, username=None):
    body = request.json

    book_id = str(uuid.uuid4())
    book = Book(book_id).from_dict(body)
    book.owner = username

    # # TODO: Save book to database
    inserted = _db.add_book(book)
    if not inserted:
        raise ApiInternalError('Fail to create book')

    # TODO: Update cache

    return json({'status': 'success'})

async def get_book(request, book_id):
    book = _db.get_book(book_id)
    if not book:
        raise ApiInternalError('Book not found')
    return json({'status': 'success', 'book': book.to_dict()})

async def update_book(request, book_id):
    body = request.json
    book = _db.get_book(book_id)
    if not book:
        raise ApiInternalError('Book not found')

    book.from_dict(body)
    updated = _db.update_book(book)
    if not updated:
        raise ApiInternalError('Fail to update book')
    return json({'status': 'success', 'book': book.to_dict()})

async def delete_book(request, book_id):
    book = _db.get_book(book_id)
    if not book:
        raise ApiInternalError('Book not found')

    deleted = _db.delete_book(book_id)
    if not deleted:
        raise ApiInternalError('Fail to delete book')
    return json({'status': 'success'})

# TODO: write api get, update, delete book
