from django.utils import translation
from django.conf import settings as django_settings
from apps.users.models import GlobalSettings


class GlobalSettingsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            settings_obj = GlobalSettings.get_settings()
            language = settings_obj.language
            translation.activate(language)
            request.LANGUAGE_CODE = translation.get_language()
            if hasattr(request, 'session'):
                request.session[translation.LANGUAGE_SESSION_KEY] = language
        except Exception:
            pass

        response = self.get_response(request)

        try:
            settings_obj = GlobalSettings.get_settings()
            response.set_cookie(
                django_settings.LANGUAGE_COOKIE_NAME,
                settings_obj.language,
                max_age=365 * 24 * 60 * 60
            )
        except Exception:
            pass

        return response
