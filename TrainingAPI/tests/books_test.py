from unittest.mock import patch

from tests.helpers import ApiTestCase, BOOK_PAYLOAD, json_body, make_book


class BooksTests(ApiTestCase):
    @patch('app.apis.books_blueprint._db')
    def test_get_all_books(self, mock_db):
        book = make_book(1).to_dict()
        mock_db.get_books_page.return_value = ([book], 1)

        _, response = self.app.test_client.get('/v1/books')

        self.assertEqual(response.status, 200)
        data = json_body(response)
        self.assertEqual(data['total'], 1)
        self.assertIsInstance(data['books'], list)
        self.assertEqual(data['books'][0]['title'], 'Test Book')

    @patch('app.apis.books_blueprint._db')
    def test_create_book_requires_auth(self, mock_db):
        _, response = self.app.test_client.post('/v1/books', json=BOOK_PAYLOAD)

        self.assertEqual(response.status, 401)
        mock_db.add_book.assert_not_called()

    @patch('app.apis.books_blueprint._db')
    def test_create_book_success(self, mock_db):
        mock_db.get_next_book_id.return_value = 1
        mock_db.add_book.return_value = True

        _, response = self.app.test_client.post(
            '/v1/books',
            json=BOOK_PAYLOAD,
            headers=self.bearer('testuser', 'user'),
        )

        self.assertEqual(response.status, 201)
        data = json_body(response)
        self.assertEqual(data['book']['owner'], 'testuser')
        self.assertEqual(data['book']['title'], 'Test Book')
        self.cache.invalidate_books.assert_awaited()

    @patch('app.apis.books_blueprint._db')
    def test_get_book_by_id(self, mock_db):
        mock_db.get_book_by_id.return_value = make_book(1)

        _, response = self.app.test_client.get('/v1/books/1')

        self.assertEqual(response.status, 200)
        self.assertEqual(json_body(response)['book']['id'], 1)

    @patch('app.apis.books_blueprint._db')
    def test_get_book_not_found(self, mock_db):
        mock_db.get_book_by_id.return_value = None

        _, response = self.app.test_client.get('/v1/books/999')

        self.assertEqual(response.status, 404)

    @patch('app.apis.books_blueprint._db')
    def test_update_book_by_owner(self, mock_db):
        mock_db.get_book_by_id.return_value = make_book(1, owner='testuser')
        mock_db.update_book.return_value = True
        updated_payload = {
            **BOOK_PAYLOAD,
            'title': 'Updated Book',
        }

        _, response = self.app.test_client.put(
            '/v1/books/1',
            json=updated_payload,
            headers=self.bearer('testuser', 'user'),
        )

        self.assertEqual(response.status, 200)
        self.assertEqual(json_body(response)['book']['title'], 'Updated Book')
        mock_db.update_book.assert_called_once()

    @patch('app.apis.books_blueprint._db')
    def test_update_book_forbidden_for_non_owner(self, mock_db):
        mock_db.get_book_by_id.return_value = make_book(1, owner='owner')

        _, response = self.app.test_client.put(
            '/v1/books/1',
            json={**BOOK_PAYLOAD, 'title': 'Hacked'},
            headers=self.bearer('otheruser', 'user'),
        )

        self.assertEqual(response.status, 403)
        mock_db.update_book.assert_not_called()

    @patch('app.apis.books_blueprint._db')
    def test_delete_book_by_owner(self, mock_db):
        mock_db.get_book_by_id.return_value = make_book(1, owner='testuser')
        mock_db.delete_book.return_value = True

        _, response = self.app.test_client.delete(
            '/v1/books/1',
            headers=self.bearer('testuser', 'user'),
        )

        self.assertEqual(response.status, 200)
        mock_db.delete_book.assert_called_once_with('1')
        self.cache.invalidate_books.assert_awaited()

    @patch('app.apis.books_blueprint._db')
    def test_delete_book_forbidden_for_non_owner(self, mock_db):
        mock_db.get_book_by_id.return_value = make_book(1, owner='owner')

        _, response = self.app.test_client.delete(
            '/v1/books/1',
            headers=self.bearer('otheruser', 'user'),
        )

        self.assertEqual(response.status, 403)
        mock_db.delete_book.assert_not_called()

    @patch('app.apis.books_blueprint._db')
    def test_admin_can_update_any_book(self, mock_db):
        mock_db.get_book_by_id.return_value = make_book(1, owner='owner')
        mock_db.update_book.return_value = True

        _, response = self.app.test_client.put(
            '/v1/books/1',
            json={**BOOK_PAYLOAD, 'title': 'Admin Updated'},
            headers=self.bearer('admin', 'admin'),
        )

        self.assertEqual(response.status, 200)
        self.assertEqual(json_body(response)['book']['title'], 'Admin Updated')
