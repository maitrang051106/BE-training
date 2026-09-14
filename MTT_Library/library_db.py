"""Seed three users and five books into the MongoDB library database."""

import os
import sys
from datetime import datetime, timezone

import django
from pymongo.errors import ServerSelectionTimeoutError


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MTT_Library.settings')
django.setup()

from library_api.databases.mongodb import MongoDB  # noqa: E402
from library_api.security.password import hash_password  # noqa: E402


USERS = [
    {'username': 'admin', 'password': 'admin12345', 'role': 'admin'},
    {'username': 'alice', 'password': 'password123', 'role': 'user'},
    {'username': 'bob', 'password': 'password123', 'role': 'user'},
]

BOOKS = [
    {
        'id': 1,
        'title': 'Clean Code',
        'authors': ['Robert C. Martin'],
        'publisher': 'Prentice Hall',
        'description': 'A handbook of agile software craftsmanship.',
        'owner': 'alice',
    },
    {
        'id': 2,
        'title': 'The Pragmatic Programmer',
        'authors': ['Andrew Hunt', 'David Thomas'],
        'publisher': 'Addison-Wesley',
        'description': 'Practical advice for software developers.',
        'owner': 'bob',
    },
    {
        'id': 3,
        'title': 'Designing Data-Intensive Applications',
        'authors': ['Martin Kleppmann'],
        'publisher': "O'Reilly Media",
        'description': 'Foundations of reliable and scalable data systems.',
        'owner': 'alice',
    },
    {
        'id': 4,
        'title': 'Refactoring',
        'authors': ['Martin Fowler'],
        'publisher': 'Addison-Wesley',
        'description': 'Improving the design of existing code.',
        'owner': 'bob',
    },
    {
        'id': 5,
        'title': 'You Do Not Talk About TypeScript',
        'authors': ['Anders Hejlsberg'],
        'publisher': 'Training Library',
        'description': 'A sample book for API CRUD practice.',
        'owner': 'admin',
    },
]


def seed_database(database=None):
    database = database or MongoDB()
    inserted_users = 0
    inserted_books = 0

    database.books.delete_many({'id': {'$regex': r'^seed-book-[1-5]$'}})

    for user in USERS:
        if database.get_user(user['username']):
            continue
        database.create_user({
            'username': user['username'],
            'password_hash': hash_password(user['password']),
            'role': user['role'],
        })
        inserted_users += 1

    now = datetime.now(timezone.utc).isoformat()
    for book in BOOKS:
        if database.get_book(book['id']):
            continue
        database.create_book({
            **book,
            'created_at': now,
            'updated_at': now,
        })
        inserted_books += 1

    return inserted_users, inserted_books


if __name__ == '__main__':
    try:
        users_count, books_count = seed_database()
    except ServerSelectionTimeoutError:
        raise SystemExit(
            'MongoDB is not running at MONGO_URI. Start MongoDB and run library_db.py again.'
        )
    print(f'Inserted users: {users_count}')
    print(f'Inserted books: {books_count}')
    print('Seed credentials: admin/admin12345, alice/password123, bob/password123')