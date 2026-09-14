import json
from unittest.mock import patch

import jwt
from django.conf import settings
from django.test import TestCase

from library_api.serializers import BookSerializer
from library_api.services.book_service import BookService
from library_api.apis.auth_api import _token_pair


class LibraryApiTests(TestCase):
    def setUp(self):
        self.book = {
            'id': 1,
            'title': 'Clean Code',
            'authors': ['Robert Martin'],
            'publisher': 'Prentice Hall',
            'description': None,
            'owner': 'alice',
        }

    def access_token(self, username='alice', role='user', jti='test-token'):
        return jwt.encode(
            {
                'username': username,
                'role': role,
                'typ': 'access',
                'jti': jti,
            },
            settings.SECRET_KEY,
            algorithm='HS256',
            headers={'kid': settings.JWT_ACTIVE_KID},
        )

    def test_api_home_and_public_book_list(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        with patch('library_api.apis.books_api.BookService') as service_class:
            service_class.return_value.list_books.return_value = [self.book]
            response = self.client.get('/books/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['n_books'], 1)

    @patch('library_api.apis.auth_api.MongoDB')
    def test_register_and_login_return_jwt(self, database_class):
        database = database_class.return_value
        database.get_user.side_effect = [None, {
            'username': 'alice',
            'password_hash': 'hash',
            'role': 'user',
        }]
        database.create_user.return_value = True
        response = self.client.post(
                '/register/',
            data=json.dumps({'username': 'alice', 'password': 'password123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        with patch('library_api.apis.auth_api.password_matches', return_value=True):
            response = self.client.post(
                '/login/',
                data=json.dumps({'username': 'alice', 'password': 'password123'}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json())

    @patch('library_api.decorators.auth.MongoDB')
    @patch('library_api.apis.books_api.BookService')
    def test_authenticated_user_can_create_owned_book(self, service_class, database_class):
        service_class.return_value.create_book.return_value = {**self.book, 'id': 6}
        database_class.return_value.is_token_revoked.return_value = False
        token = jwt.encode(
            {'username': 'alice', 'role': 'user', 'typ': 'access', 'jti': 'test-create'},
            settings.SECRET_KEY, algorithm='HS256', headers={'kid': settings.JWT_ACTIVE_KID}
        )
        response = self.client.post(
            '/books/create/',
            data=json.dumps({
                'title': 'Clean Code',
                'authors': ['Robert Martin'],
                'publisher': 'Prentice Hall',
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['book']['owner'], 'alice')

    @patch('library_api.decorators.auth.MongoDB')
    @patch('library_api.apis.books_api.BookService')
    def test_owner_can_update_book_on_resource_path(self, service_class, database_class):
        service = service_class.return_value
        service.get_book.return_value = self.book.copy()
        service.update_book.return_value = {**self.book, 'title': 'Clean Architecture'}
        database_class.return_value.is_token_revoked.return_value = False
        token = jwt.encode(
            {'username': 'alice', 'role': 'user', 'typ': 'access', 'jti': 'test-update'},
            settings.SECRET_KEY, algorithm='HS256', headers={'kid': settings.JWT_ACTIVE_KID}
        )
        response = self.client.put(
            '/books/1/',
            data=json.dumps({
                'title': 'Clean Architecture',
                'authors': ['Robert Martin'],
                'publisher': 'Pearson',
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['book']['title'], 'Clean Architecture')

    def test_missing_jwt_is_rejected(self):
        response = self.client.post('/books/create/', data='{}', content_type='application/json')
        self.assertEqual(response.status_code, 401)

    @patch('library_api.apis.auth_api.MongoDB')
    def test_invalid_login_is_rejected(self, database_class):
        database_class.return_value.get_user.return_value = None
        response = self.client.post(
            '/login/',
            data=json.dumps({'username': 'alice', 'password': 'wrongpass'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    @patch('library_api.decorators.auth.MongoDB')
    @patch('library_api.apis.books_api.BookService')
    def test_invalid_book_payload_returns_400(self, service_class, database_class):
        database_class.return_value.is_token_revoked.return_value = False
        response = self.client.post(
            '/books/create/',
            data=json.dumps({'title': '', 'authors': [], 'publisher': ''}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token()}',
        )
        self.assertEqual(response.status_code, 400)
        service_class.return_value.create_book.assert_not_called()

    @patch('library_api.decorators.auth.MongoDB')
    @patch('library_api.apis.books_api.BookService')
    def test_non_owner_cannot_update_book(self, service_class, database_class):
        database_class.return_value.is_token_revoked.return_value = False
        service_class.return_value.get_book.return_value = {**self.book, 'owner': 'bob'}
        response = self.client.put(
            '/books/1/',
            data=json.dumps({
                'title': 'Changed',
                'authors': ['Author'],
                'publisher': 'Publisher',
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token(username="alice", jti="not-owner")}',
        )
        self.assertEqual(response.status_code, 403)
        service_class.return_value.update_book.assert_not_called()

    @patch('library_api.decorators.auth.MongoDB')
    @patch('library_api.apis.auth_api.MongoDB')
    def test_non_admin_cannot_list_users(self, auth_database, decorator_database):
        decorator_database.return_value.is_token_revoked.return_value = False
        response = self.client.get(
            '/admin/users/',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token()}',
        )
        self.assertEqual(response.status_code, 403)
        auth_database.return_value.list_users.assert_not_called()

    @patch('library_api.decorators.auth.MongoDB')
    @patch('library_api.apis.auth_api.MongoDB')
    def test_admin_can_list_users(self, auth_database, decorator_database):
        decorator_database.return_value.is_token_revoked.return_value = False
        auth_database.return_value.list_users.return_value = [
            {'username': 'alice', 'role': 'user'},
        ]
        response = self.client.get(
            '/admin/users/',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token(username="admin", role="admin", jti="admin-list")}',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['users'][0]['username'], 'alice')

    def test_book_service_uses_cache_and_invalidates_after_create(self):
        book_data = self.book
        repository = type('Repository', (), {
            'list_books': lambda self: [book_data],
            'create_book': lambda self, book: True,
            'get_next_book_id': lambda self: 6,
        })()
        cached = {}
        book_cache = type('BookCache', (), {
            'get_list': classmethod(lambda cls: cached.get('list')),
            'set_list': classmethod(lambda cls, books: cached.update(list=books)),
            'invalidate': classmethod(lambda cls, id=None: cached.clear()),
        })
        service = BookService(database=repository, book_cache=book_cache)

        self.assertEqual(service.list_books(), [self.book])
        self.assertEqual(service.list_books(), [self.book])
        service.create_book({
            'title': 'Refactoring',
            'authors': ['Martin Fowler'],
            'publisher': 'Addison-Wesley',
        }, 'alice')
        self.assertEqual(cached, {})

    def test_book_serializer_rejects_blank_title(self):
        serializer = BookSerializer(data={
            'title': ' ',
            'authors': ['Author'],
            'publisher': 'Publisher',
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    @patch('library_api.apis.auth_api.MongoDB')
    def test_admin_login_returns_access_and_refresh_tokens(self, database_class):
        database_class.return_value.get_user.return_value = {
            'username': 'admin', 'password_hash': 'hash', 'role': 'admin'
        }
        with patch('library_api.apis.auth_api.password_matches', return_value=True):
            response = self.client.post(
                '/login/',
                data=json.dumps({'username': 'admin', 'password': 'admin12345'}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', response.json())
        self.assertIn('refresh_token', response.json())
        self.assertEqual(jwt.decode(
            response.json()['access_token'], settings.SECRET_KEY,
            algorithms=['HS256'], options={'verify_exp': False},
        )['role'], 'admin')

    @patch('library_api.apis.auth_api.MongoDB')
    def test_refresh_rotates_and_revokes_old_refresh_token(self, database_class):
        pair = _token_pair('alice', 'user')
        database_class.return_value.is_token_revoked.return_value = False
        response = self.client.post(
            '/refresh/',
            data=json.dumps({'refresh_token': pair['refresh_token']}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        database_class.return_value.revoke_token.assert_called_once()
        self.assertNotEqual(response.json()['refresh_token'], pair['refresh_token'])

    @patch('library_api.decorators.auth.MongoDB')
    @patch('library_api.apis.auth_api.MongoDB')
    def test_logout_revokes_access_token(self, auth_database, decorator_database):
        pair = _token_pair('alice', 'user')
        claims = pair['_claims'][0]
        decorator_database.return_value.is_token_revoked.return_value = False
        response = self.client.post(
            '/logout/',
            data=json.dumps({'refresh_token': pair['refresh_token']}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {pair['access_token']}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(auth_database.return_value.revoke_token.called)
        revoked_ids = [call.args[0] for call in auth_database.return_value.revoke_token.call_args_list]
        self.assertIn(claims['jti'], revoked_ids)
        self.assertEqual(len(revoked_ids), 2)