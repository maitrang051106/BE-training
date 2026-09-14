from datetime import datetime, timezone
def build_book(payload, owner, book_id):
    now = datetime.now(timezone.utc).isoformat()
    return {
        'id': int(book_id),
        'title': payload['title'].strip(),
        'authors': [author.strip() for author in payload['authors']],
        'publisher': payload['publisher'].strip(),
        'description': payload.get('description'),
        'owner': owner,
        'created_at': now,
        'updated_at': now,
    }