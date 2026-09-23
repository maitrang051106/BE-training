import json
import os
from unittest.mock import AsyncMock, patch

os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-unittest')

import unittest

from app.models.book import Book
from app.utils.jwt_utils import generate_token_pair


BOOK_PAYLOAD = {
    'title': 'Test Book',
    'authors': ['Author One'],
    'publisher': 'Test Publisher',
    'description': 'A test book',
}


def json_body(response):
    raw = response.body if response.body is not None else response.text
    if isinstance(raw, bytes):
        raw = raw.decode()
    return json.loads(raw)


def make_book(book_id=1, owner='testuser'):
    book = Book(book_id)
    book.from_dict(BOOK_PAYLOAD)
    book.owner = owner
    return book


class ApiTestCase(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls):
        from main import app

        cls.app = app

    def setUp(self):
        self.cache = AsyncMock()
        self.cache.connect = AsyncMock()
        self.cache.disconnect = AsyncMock()
        self.cache.is_jwt_revoked = AsyncMock(return_value=False)
        self.cache.revoke_jwt = AsyncMock()
        self.cache.get = AsyncMock(return_value=None)
        self.cache.set = AsyncMock()
        self.cache.delete = AsyncMock()
        self.cache.invalidate_books = AsyncMock()

        self._redis_patch = patch('app.hooks.setup_.RedisCache', return_value=self.cache)
        self._redis_patch.start()

    def tearDown(self):
        self._redis_patch.stop()

    def bearer(self, username='testuser', role='user'):
        token = generate_token_pair(username, role)['access_token']
        return {'Authorization': f'Bearer {token}'}

    def token_pair(self, username='testuser', role='user'):
        return generate_token_pair(username, role)
