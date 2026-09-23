from django.http import JsonResponse


def api_error(message, status):
    return JsonResponse({'status': 'error', 'message': message}, status=status)