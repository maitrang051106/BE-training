import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from library_api.decorators.auth import require_jwt
from library_api.hooks.error import api_error
from library_api.serializers import BookSerializer
from library_api.services.book_service import BookService


def _service():
    return BookService()


def _payload(request):
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return None


@csrf_exempt
@require_http_methods(['GET'])
def list_books(request):
    books = _service().list_books()
    return JsonResponse({'status': 'success', 'n_books': len(books), 'books': books})


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'DELETE'])
def get_book(request, id):
    if request.method != 'GET':
        return manage_book(request, id)
    book = _service().get_book(id)
    if not book:
        return api_error('Book not found', 404)
    return JsonResponse({'status': 'success', 'book': book})


@csrf_exempt
@require_jwt
@require_http_methods(['POST'])
def create_book(request):
    serializer = BookSerializer(data=_payload(request))
    if not serializer.is_valid():
        return JsonResponse({'status': 'error', 'errors': serializer.errors}, status=400)
    book = _service().create_book(serializer.validated_data, request.user_claims['username'])
    if not book:
        return api_error('Unable to create book', 500)
    return JsonResponse({'status': 'success', 'book': book}, status=201)


@csrf_exempt
@require_jwt
@require_http_methods(['PUT', 'DELETE'])
def manage_book(request, id):
    service = _service()
    book = service.get_book(id)
    if not book:
        return api_error('Book not found', 404)
    claims = request.user_claims
    if claims.get('role') != 'admin' and book.get('owner') != claims.get('username'):
        return api_error('Permission denied', 403)

    if request.method == 'DELETE':
        if not service.delete_book(id):
            return api_error('Unable to delete book', 500)
        return JsonResponse({'status': 'success'})

    serializer = BookSerializer(data=_payload(request))
    if not serializer.is_valid():
        return JsonResponse({'status': 'error', 'errors': serializer.errors}, status=400)
    updated_book = service.update_book(id, serializer.validated_data)
    if not updated_book:
        return api_error('Unable to update book', 500)
    return JsonResponse({'status': 'success', 'book': updated_book})