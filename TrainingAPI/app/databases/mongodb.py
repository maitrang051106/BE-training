from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from app.constants.mongodb_constants import MongoCollections
from app.models.book import Book
from app.utils.logger_utils import get_logger
from config import MongoDBConfig

logger = get_logger('MongoDB')


class MongoDB:
    def __init__(self, connection_url=None):
        if connection_url is None:
            connection_url = MongoDBConfig.CONNECTION_URL

        self.connection_url = connection_url.split('@')[-1]
        self.client = MongoClient(connection_url)
        self.db = self.client[MongoDBConfig.DATABASE]

        self._books_col = self.db[MongoCollections.books]
        self._users_col = self.db[MongoCollections.users]
        self._users_col.create_index('username', unique=True)

    def get_books(self, filter_=None, projection=None):
        try:
            if not filter_:
                filter_ = {}
            cursor = self._books_col.find(filter_, projection=projection)
            data = []
            for doc in cursor:
                data.append(Book().from_dict(doc))
            return data
        except Exception as ex:
            logger.exception(ex)
        return []

    def add_book(self, book: Book):
        try:
            inserted_doc = self._books_col.insert_one(book.to_dict())
            return inserted_doc
        except Exception as ex:
            logger.exception(ex)
        return None

    def get_book_by_id(self, id: str):
        try:
            doc = self._books_col.find_one({'id': id})
            if doc:
                return Book().from_dict(doc)
        except Exception as ex:
            logger.exception(ex)
        return None

    def update_book(self, id: str, updated_data: dict):
        try:
            result = self._books_col.update_one({'id': id}, {'$set': updated_data})
            return result.matched_count > 0
        except Exception as ex:
            logger.exception(ex)
        return False

    def delete_book(self, id: str):
        try:
            result = self._books_col.delete_one({'id': id})
            return result.deleted_count > 0
        except Exception as ex:
            logger.exception(ex)
        return False

    def get_user(self, username: str):
        try:
            return self._users_col.find_one({'username': username})
        except Exception as ex:
            logger.exception(ex)
        return None

    def add_user(self, username: str, password_hash: str, role: str = 'user'):
        try:
            return self._users_col.insert_one({
                'username': username,
                'password_hash': password_hash,
                'role': role
            })
        except DuplicateKeyError:
            return None
        except Exception as ex:
            logger.exception(ex)
        return None

    def get_users(self):
        try:
            return list(self._users_col.find({}, {'_id': 0, 'password_hash': 0}))
        except Exception as ex:
            logger.exception(ex)
        return []

    def update_user(self, username: str, updated_data: dict):
        try:
            result = self._users_col.update_one(
                {'username': username},
                {'$set': updated_data}
            )
            return result.matched_count > 0
        except Exception as ex:
            logger.exception(ex)
        return False

    def delete_user(self, username: str):
        try:
            result = self._users_col.delete_one({'username': username})
            return result.deleted_count > 0
        except Exception as ex:
            logger.exception(ex)
        return False
    # TODO: write functions CRUD with books
