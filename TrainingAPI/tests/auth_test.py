import bcrypt
from unittest.mock import AsyncMock, patch

from tests.helpers import ApiTestCase, json_body


class AuthTests(ApiTestCase):
    @patch('app.apis.auth_blueprint._db')
    def test_register_success(self, mock_db):
        mock_db.get_user.return_value = None
        mock_db.add_user.return_value = True

        _, response = self.app.test_client.post(
            '/v1/auth/register',
            json={'username': 'newuser', 'password': 'password123'},
        )

        self.assertEqual(response.status, 201)
        data = json_body(response)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['username'], 'newuser')
        mock_db.add_user.assert_called_once()

    @patch('app.apis.auth_blueprint._db')
    def test_register_duplicate_username(self, mock_db):
        mock_db.get_user.return_value = {'username': 'newuser'}

        _, response = self.app.test_client.post(
            '/v1/auth/register',
            json={'username': 'newuser', 'password': 'password123'},
        )

        self.assertEqual(response.status, 400)
        self.assertIn('already exists', json_body(response)['error']['message'])

    @patch('app.apis.auth_blueprint._db')
    def test_login_success(self, mock_db):
        password_hash = bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode('utf-8')
        mock_db.get_user.return_value = {
            'username': 'testuser',
            'password_hash': password_hash,
            'role': 'user',
        }

        _, response = self.app.test_client.post(
            '/v1/auth/login',
            json={'username': 'testuser', 'password': 'password123'},
        )

        self.assertEqual(response.status, 200)
        data = json_body(response)
        self.assertEqual(data['status'], 'success')
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
        self.assertEqual(data['token_type'], 'Bearer')

    @patch('app.apis.auth_blueprint._db')
    def test_login_invalid_credentials(self, mock_db):
        mock_db.get_user.return_value = None

        _, response = self.app.test_client.post(
            '/v1/auth/login',
            json={'username': 'testuser', 'password': 'wrongpass'},
        )

        self.assertEqual(response.status, 401)

    @patch('app.apis.auth_blueprint._db')
    def test_refresh_token_success(self, mock_db):
        tokens = self.token_pair('testuser', 'user')
        mock_db.get_user.return_value = {
            'username': 'testuser',
            'password_hash': 'hash',
            'role': 'user',
        }

        _, response = self.app.test_client.post(
            '/v1/auth/refresh',
            json={'refresh_token': tokens['refresh_token']},
        )

        self.assertEqual(response.status, 200)
        data = json_body(response)
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
        self.cache.revoke_jwt.assert_awaited()

    @patch('app.apis.auth_blueprint._db')
    def test_refresh_token_rejects_revoked(self, mock_db):
        tokens = self.token_pair('testuser', 'user')
        self.cache.is_jwt_revoked = AsyncMock(return_value=True)

        _, response = self.app.test_client.post(
            '/v1/auth/refresh',
            json={'refresh_token': tokens['refresh_token']},
        )

        self.assertEqual(response.status, 401)
        mock_db.get_user.assert_not_called()

    @patch('app.apis.auth_blueprint._db')
    def test_logout_revokes_access_token(self, mock_db):
        tokens = self.token_pair('testuser', 'user')

        _, response = self.app.test_client.post(
            '/v1/auth/logout',
            headers={'Authorization': f"Bearer {tokens['access_token']}"},
        )

        self.assertEqual(response.status, 200)
        self.assertEqual(json_body(response)['status'], 'success')
        self.cache.revoke_jwt.assert_awaited()

    @patch('app.apis.auth_blueprint._db')
    def test_logout_revokes_refresh_token_when_provided(self, mock_db):
        tokens = self.token_pair('testuser', 'user')

        _, response = self.app.test_client.post(
            '/v1/auth/logout',
            headers={'Authorization': f"Bearer {tokens['access_token']}"},
            json={'refresh_token': tokens['refresh_token']},
        )

        self.assertEqual(response.status, 200)
        self.assertEqual(self.cache.revoke_jwt.await_count, 2)

    @patch('app.apis.auth_blueprint._db')
    def test_admin_get_users(self, mock_db):
        mock_db.get_users.return_value = [
            {'username': 'admin', 'role': 'admin'},
            {'username': 'testuser', 'role': 'user'},
        ]

        _, response = self.app.test_client.get(
            '/v1/auth/users',
            headers=self.bearer('admin', 'admin'),
        )

        self.assertEqual(response.status, 200)
        data = json_body(response)
        self.assertEqual(len(data['users']), 2)

    @patch('app.apis.auth_blueprint._db')
    def test_admin_create_user(self, mock_db):
        mock_db.get_user.return_value = None
        mock_db.add_user.return_value = True

        _, response = self.app.test_client.post(
            '/v1/auth/users',
            headers=self.bearer('admin', 'admin'),
            json={'username': 'bob', 'password': 'password123', 'role': 'user'},
        )

        self.assertEqual(response.status, 201)
        self.assertEqual(json_body(response)['username'], 'bob')
        mock_db.add_user.assert_called_once()
        username, _password_hash, role = mock_db.add_user.call_args[0]
        self.assertEqual(username, 'bob')
        self.assertEqual(role, 'user')

    @patch('app.apis.auth_blueprint._db')
    def test_admin_update_user(self, mock_db):
        mock_db.update_user.return_value = True

        _, response = self.app.test_client.put(
            '/v1/auth/users/bob',
            headers=self.bearer('admin', 'admin'),
            json={'password': 'newpassword123', 'role': 'admin'},
        )

        self.assertEqual(response.status, 200)
        self.assertEqual(json_body(response)['username'], 'bob')
        updated_data = mock_db.update_user.call_args[0][1]
        self.assertEqual(updated_data['role'], 'admin')
        self.assertIn('password_hash', updated_data)

    @patch('app.apis.auth_blueprint._db')
    def test_admin_delete_user(self, mock_db):
        mock_db.delete_user.return_value = True

        _, response = self.app.test_client.delete(
            '/v1/auth/users/bob',
            headers=self.bearer('admin', 'admin'),
        )

        self.assertEqual(response.status, 200)
        mock_db.delete_user.assert_called_once_with('bob')

    @patch('app.apis.auth_blueprint._db')
    def test_non_admin_cannot_create_user(self, mock_db):
        _, response = self.app.test_client.post(
            '/v1/auth/users',
            headers=self.bearer('testuser', 'user'),
            json={'username': 'bob', 'password': 'password123'},
        )

        self.assertEqual(response.status, 403)
        mock_db.add_user.assert_not_called()

    @patch('app.apis.auth_blueprint._db')
    def test_admin_cannot_delete_self(self, mock_db):
        _, response = self.app.test_client.delete(
            '/v1/auth/users/admin',
            headers=self.bearer('admin', 'admin'),
        )

        self.assertEqual(response.status, 400)
        mock_db.delete_user.assert_not_called()

    @patch('app.apis.auth_blueprint._db')
    def test_protected_route_rejects_revoked_token(self, mock_db):
        self.cache.is_jwt_revoked = AsyncMock(return_value=True)

        _, response = self.app.test_client.get(
            '/v1/auth/users',
            headers=self.bearer('admin', 'admin'),
        )

        self.assertEqual(response.status, 401)
        mock_db.get_users.assert_not_called()
