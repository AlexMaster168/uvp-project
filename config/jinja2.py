from django.urls import reverse
from django.templatetags.static import static
from jinja2 import Environment

def url(viewname, *args, **kwargs):
    return reverse(viewname, args=args, kwargs=kwargs)


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': url,
    })
    return env
