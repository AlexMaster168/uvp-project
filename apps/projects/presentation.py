"""View registry: add layouts here without duplicating selectors in templates."""
PROJECT_LIST_MODES = (
    ('1', 'Картки', 'cards'),
    ('2', 'Компактні картки', 'cards'),
    ('3', 'Для керівництва · темний', 'report'),
    ('4', 'Для керівництва · світлий', 'report'),
    ('5', 'Таблиця проєктів', 'table'),
    ('6', 'Дошка за статусами', 'board'),
    ('7', 'Сучасний огляд', 'medusa'),
)
REPORT_TASK_LAYOUTS = (('cards', 'Вид 1 · Картки'), ('rows', 'Вид 2 · Рядки'))


def project_list_mode(value):
    return next((entry for entry in PROJECT_LIST_MODES if entry[0] == value), PROJECT_LIST_MODES[0])
