from django.core.cache import cache


class BookCache:
    list_key = 'library:books:list'

    @classmethod
    def get_list(cls):
        return cache.get(cls.list_key)

    @classmethod
    def set_list(cls, books, timeout=300):
        cache.set(cls.list_key, books, timeout=timeout)

    @classmethod
    def get_detail(cls, id):
        return cache.get(f'library:book:{id}')

    @classmethod
    def set_detail(cls, id, book, timeout=300):
        cache.set(f'library:book:{id}', book, timeout=timeout)

    @classmethod
    def invalidate(cls, id=None):
        cache.delete(cls.list_key)
        if id:
            cache.delete(f'library:book:{id}')