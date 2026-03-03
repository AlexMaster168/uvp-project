from django.urls import reverse
from django.templatetags.static import static
from jinja2 import Environment
from apps.users.models import GlobalSettings


def url(viewname, *args, **kwargs):
    return reverse(viewname, args=args, kwargs=kwargs)


def get_global_settings():
    try:
        return GlobalSettings.get_settings()
    except Exception:
        class DummySettings:
            theme = 'bg-gradient-1'
            language = 'ru'

        return DummySettings()


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': url,
        'get_global_settings': get_global_settings,
    })
    return env
