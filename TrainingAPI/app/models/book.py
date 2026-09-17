from app.utils.datetime_utils import normalize_timestamp, utc_now_iso


class Book:
    def __init__(self, id=''):
        self.id = id
        self.title = ''
        self.authors = []
        self.publisher = ''
        self.description = None
        self.owner = None
        now = utc_now_iso()
        self.created_at = now
        self.last_updated_at = now

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
        self.title = json_dict.get('title', '').strip()
        self.authors = [author.strip() for author in json_dict.get('authors', [])]
        self.publisher = json_dict.get('publisher', '').strip()
        description = json_dict.get('description')
        self.description = description.strip() if isinstance(description, str) else description
        self.owner = json_dict.get('owner')
        self.created_at = normalize_timestamp(json_dict.get('createdAt'))
        self.last_updated_at = normalize_timestamp(json_dict.get('lastUpdatedAt'))
        return self


create_book_json_schema = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'title': {'type': 'string', 'pattern': r'\S', 'maxLength': 255},
        'authors': {
            'type': 'array',
            'minItems': 1,
            'items': {'type': 'string', 'pattern': r'\S', 'maxLength': 255}
        },
        'publisher': {'type': 'string', 'pattern': r'\S', 'maxLength': 255},
        'description': {'type': 'string', 'maxLength': 2000},
    },
    'required': ['title', 'authors', 'publisher']
}
