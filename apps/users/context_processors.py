from apps.users.models import GlobalSettings


def global_settings_processor(request):
    try:
        settings = GlobalSettings.get_settings()
    except Exception:
        class DummySettings:
            theme = 'bg-gradient-1'
            language = 'ru'

        settings = DummySettings()
    return {'global_settings': settings}
