from django.urls import reverse
from django.templatetags.static import static
from django.utils.translation import get_language
from django.utils.translation import gettext as django_gettext
from jinja2 import Environment

TRANSLATIONS = {
    'en': {
        'УВП': 'UVP',
        'Проекты': 'Projects',
        'Задачи': 'Tasks',
        'Финансы': 'Finance',
        'Доступы': 'Access',
        'Медиа': 'Media',
        'Пользователи': 'Users',
        'Настройки': 'Settings',
        'Гость': 'Guest',
        'Профиль': 'Profile',
        'Выйти': 'Logout',
        'Войти': 'Login',
        'Сохранить': 'Save',
        'Глобальные настройки системы': 'Global System Settings',
        'Тема': 'Theme',
        'Язык': 'Language',
    },
    'uk': {
        'УВП': 'УВП',
        'Проекты': 'Проєкти',
        'Задачи': 'Завдання',
        'Финансы': 'Фінанси',
        'Доступы': 'Доступи',
        'Медиа': 'Медіа',
        'Пользователи': 'Користувачі',
        'Настройки': 'Налаштування',
        'Гость': 'Гість',
        'Профиль': 'Профіль',
        'Выйти': 'Вийти',
        'Войти': 'Увійти',
        'Сохранить': 'Зберегти',
        'Глобальные настройки системы': 'Глобальні налаштування системи',
        'Тема': 'Тема',
        'Язык': 'Мова',
    }
}


def _(text):
    lang = get_language()
    if lang in TRANSLATIONS and text in TRANSLATIONS[lang]:
        return TRANSLATIONS[lang][text]
    return django_gettext(text)


def url(viewname, *args, **kwargs):
    return reverse(viewname, args=args, kwargs=kwargs)


def get_global_settings():
    try:
        from apps.users.models import GlobalSettings
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
        '_': _,
    })
    return env
