import os


class LogHostnameMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        container_name = os.getenv('HOSTNAME')  # Docker sets the hostname environment variable
        print(f"Served by container: {container_name}", flush=True)

        response = self.get_response(request)
        return response
