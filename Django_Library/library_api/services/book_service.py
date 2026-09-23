from library_api.cache.book_cache import BookCache
from library_api.databases.mongodb import MongoDB
from library_api.models.book import build_book


class BookService:
    def __init__(self, database=None, book_cache=None):
        self.database = database or MongoDB()
        self.book_cache = book_cache or BookCache

    def list_books(self):
        books = self.book_cache.get_list()
        if books is None:
            books = self.database.list_books()
            self.book_cache.set_list(books)
        return books

    def get_book(self, id):
        book = self.book_cache.get_detail(id)
        if book is None:
            book = self.database.get_book(id)
            if book:
                self.book_cache.set_detail(id, book)
        return book

    def create_book(self, payload, owner):
        book = build_book(payload, owner, self.database.get_next_book_id())
        if not self.database.create_book(book):
            return None
        self.book_cache.invalidate()
        return book

    def update_book(self, id, payload):
        current_book = self.database.get_book(id)
        if not current_book:
            return None
        updates = {
            'title': payload['title'].strip(),
            'authors': [author.strip() for author in payload['authors']],
            'publisher': payload['publisher'].strip(),
            'description': payload.get('description'),
        }
        if not self.database.update_book(id, updates):
            return None
        self.book_cache.invalidate(id)
        current_book.update(updates)
        self.book_cache.set_detail(id, current_book)
        return current_book

    def delete_book(self, id):
        deleted = self.database.delete_book(id)
        if deleted:
            self.book_cache.invalidate(id)
        return deleted