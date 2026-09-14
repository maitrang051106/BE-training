import time


class Book:
    def __init__(self, id=''):
        self.id = id
        self.title = ''
        self.authors = []
        self.publisher = ''
        self.description = None
        self.owner = None
        self.created_at = int(time.time())
        self.last_updated_at = int(time.time())

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'publisher': self.publisher,
            'description': self.description,
            'owner': self.owner,
            'createdAt': self.created_at,
            'lastUpdatedAt': self.last_updated_at
        }

    def from_dict(self, json_dict: dict):
        self.id = json_dict.get('id', self.id)
        self.title = json_dict.get('title', '')
        self.authors = json_dict.get('authors', [])
        self.publisher = json_dict.get('publisher', '')
        self.description = json_dict.get('description')
        self.owner = json_dict.get('owner')
        self.created_at = json_dict.get('createdAt', int(time.time()))
        self.last_updated_at = json_dict.get('lastUpdatedAt', int(time.time()))
        return self


create_book_json_schema = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'title': {'type': 'string', 'minLength': 1, 'maxLength': 255},
        'authors': {
            'type': 'array',
            'minItems': 1,
            'items': {'type': 'string', 'minLength': 1, 'maxLength': 255}
        },
        'publisher': {'type': 'string', 'minLength': 1, 'maxLength': 255},
        'description': {'type': 'string', 'maxLength': 2000},
    },
    'required': ['title', 'authors', 'publisher']
}
