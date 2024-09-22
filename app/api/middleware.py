from django.urls import resolve

class DisableCSRF:
    """
    Middleware for disabling CSRF in a specified app name.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        app_name = "api"
        if resolve(request.path_info).app_name == app_name:
            setattr(request, '_dont_enforce_csrf_checks', True)
        response = self.get_response(request)
        return response