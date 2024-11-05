from django.shortcuts import redirect
from django.conf import settings
from django.urls import resolve

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ignorujeme přihlašovací, registrační nebo odhlašovací URL
        exempt_urls = [settings.LOGIN_URL, '/register/', '/logout/']  # upravte podle potřeby
        if not request.user.is_authenticated and request.path not in exempt_urls:
            return redirect(settings.LOGIN_URL)
        return self.get_response(request)
