from django.http import JsonResponse


def ratelimit_view(request, exception=None):
    return JsonResponse({'error': 'Too many requests, please try again later.'}, status=429)
