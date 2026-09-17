class CacheConstants:
    all_books = 'all_books'

    def books_key(page, per_page, filters):
        filter_key = '&'.join(f'{key}={filters[key]}' for key in sorted(filters))
        return f'books:{page}:{per_page}:{filter_key}'
