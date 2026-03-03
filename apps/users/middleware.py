from django.utils import translation
from apps.users.models import GlobalSettings


class GlobalSettingsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            settings = GlobalSettings.get_settings()
            translation.activate(settings.language)
            request.LANGUAGE_CODE = translation.get_language()
        except Exception:
            pass
        return self.get_response(request)
