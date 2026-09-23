import os
from functools import lru_cache
from threading import Lock

from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError

from library_api.constants.mongodb_constants import MongoCollections


@lru_cache(maxsize=4)
def _mongo_client(connection_url):
    return MongoClient(connection_url, serverSelectionTimeoutMS=2000)


class MongoDB:
    _index_lock = Lock()
    _indexed_databases = set()

    def __init__(self):
        connection_url = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        self.client = _mongo_client(connection_url)
        database_name = os.getenv('MONGO_DATABASE', 'training_django')
        self.database = self.client[database_name]
        self.users = self.database[MongoCollections.users]
        self.books = self.database[MongoCollections.books]
        self.counters = self.database[MongoCollections.counters]
        self.revoked_tokens = self.database[MongoCollections.revoked_tokens]
        index_key = f'{connection_url}/{database_name}'
        if index_key not in self._indexed_databases:
            with self._index_lock:
                if index_key not in self._indexed_databases:
                    self.users.create_index('username', unique=True)
                    self.books.create_index('id', unique=True)
                    self.revoked_tokens.create_index('jti', unique=True)
                    self.revoked_tokens.create_index('expires_at', expireAfterSeconds=0)
                    self._indexed_databases.add(index_key)

    def get_user(self, username):
        return self.users.find_one({'username': username}, {'_id': 0})

    def create_user(self, user):
        try:
            self.users.insert_one(user)
            return True
        except DuplicateKeyError:
            return False

    def list_users(self):
        return list(self.users.find({}, {'_id': 0, 'password_hash': 0}))

    def update_user(self, username, updates):
        result = self.users.update_one({'username': username}, {'$set': updates})
        return result.matched_count > 0

    def delete_user(self, username):
        result = self.users.delete_one({'username': username})
        return result.deleted_count > 0

    def revoke_token(self, jti, expires_at):
        self.revoked_tokens.update_one(
            {'jti': jti},
            {'$set': {'jti': jti, 'expires_at': expires_at}},
            upsert=True,
        )

    def is_token_revoked(self, jti):
        return self.revoked_tokens.find_one({'jti': jti}, {'_id': 1}) is not None

    def list_books(self):
        return list(self.books.find({}, {'_id': 0}))

    def get_next_book_id(self):
        counter = self.counters.find_one({'_id': 'books'})
        if counter is None:
            latest = self.books.find_one(
                {'id': {'$type': 'number'}},
                {'id': 1},
                sort=[('id', -1)],
            )
            self.counters.update_one(
                {'_id': 'books'},
                {'$setOnInsert': {'value': latest['id'] if latest else 0}},
                upsert=True,
            )
        counter = self.counters.find_one_and_update(
            {'_id': 'books'},
            {'$inc': {'value': 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return counter['value']

    def get_book(self, id):
        return self.books.find_one({'id': int(id)}, {'_id': 0})

    def create_book(self, book):
        try:
            self.books.insert_one(book)
            return True
        except DuplicateKeyError:
            return False

    def update_book(self, id, updates):
        result = self.books.update_one({'id': int(id)}, {'$set': updates})
        return result.matched_count > 0

    def delete_book(self, id):
        result = self.books.delete_one({'id': int(id)})
        return result.deleted_count > 0