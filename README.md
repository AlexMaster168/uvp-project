# УВП - Система Управления Временем Проектов

## Описание
Веб-приложение для управления проектами, задачами, финансами и доступами с визуализацией структуры проекта.

## Стек технологий
- **Backend**: Django 5.x + Django REST Framework
- **Frontend**: Jinja2 Templates + HTMX + Alpine.js
- **Database**: PostgreSQL
- **Visualization**: Rete.js
- **Storage**: MinIO / S3 (опционально)

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка базы данных

Создайте PostgreSQL базу данных:
```bash
createdb uvp_db
```

Или используйте SQLite для разработки (по умолчанию в settings.py).

### 3. Применение миграций

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Создание суперпользователя

```bash
python manage.py createsuperuser
```

### 5. Загрузка статики

```bash
python manage.py collectstatic --noinput
```

### 6. Запуск сервера

```bash
python manage.py runserver
```

Приложение будет доступно по адресу: `http://127.0.0.1:8000`

## Структура проекта

```
uvp_project/
├── config/              # Настройки Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── users/          # Управление пользователями и правами
│   ├── projects/       # Проекты и связанные сущности
│   ├── tasks/          # Задачи
│   ├── billing/        # Финансы
│   ├── access/         # Доступы к внешним ресурсам
│   └── media_files/    # Медиафайлы
├── templates/          # Jinja2 шаблоны
├── static/            # Статические файлы (CSS, JS)
└── media/             # Загружаемые файлы

## Роли и права доступа

### Глобальные роли:
- **sa** (super admin) - полный доступ ко всему
- **admin** - управление своими проектами и пользователями
- **manager** - управление проектами с ограничениями
- **guest** - только просмотр

### Проектные роли:
- **owner** - владелец проекта, полный доступ
- **manager** - менеджер проекта
- **member** - участник проекта
- **viewer** - наблюдатель (только чтение)

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Вход
- `POST /api/auth/logout/` - Выход

### Projects
- `GET /api/projects/` - Список проектов
- `POST /api/projects/` - Создать проект
- `GET /api/projects/<id>/` - Детали проекта
- `PUT/PATCH /api/projects/<id>/` - Обновить проект
- `DELETE /api/projects/<id>/` - Удалить проект
- `GET/POST /api/projects/<id>/structure/` - Структура для Rete.js

### Tasks
- `GET /api/tasks/` - Список задач
- `POST /api/tasks/` - Создать задачу
- `GET /api/tasks/<id>/` - Детали задачи
- `PATCH /api/tasks/<id>/` - Обновить задачу

### Tags
- `GET /api/tags/` - Список тегов (с поиском)
- `POST /api/tags/` - Создать тег

### Users
- `GET /api/users/` - Список пользователей (с поиском)
- `POST /api/users/` - Создать пользователя

## Основные страницы

- `/` - Главная страница
- `/projects/` - Список проектов
- `/projects/<id>/` - Детали проекта (вкладки: Tasks, Billing, Access, Media, Structure)
- `/projects/<id>/edit/` - Редактирование проекта
- `/tasks/` - Список задач
- `/billing/` - Финансы
- `/access/` - Доступы
- `/structure/<project_id>/` - Визуализация структуры (Rete.js)

## Разработка

### Создание миграций после изменения моделей
```bash
python manage.py makemigrations
python manage.py migrate
```

### Запуск тестов
```bash
python manage.py test
```

### Создание фикстур (тестовых данных)
```bash
python manage.py loaddata fixtures/initial_data.json
```

## Docker (опционально)

```bash
docker-compose up -d
```

## Лицензия
Proprietary
