from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from jinja2 import Environment


def environment(**options):
    env = Environment(**options)
    def jinja_url(viewname, *args, **kwargs):
        return reverse(viewname, args=args, kwargs=kwargs)

    env.globals.update({
        'static': staticfiles_storage.url,
        'url': jinja_url,
    })
    return env