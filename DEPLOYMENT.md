# Полная инструкция по развёртыванию УВП

## 📋 Оглавление
1. [Подготовка окружения](#подготовка-окружения)
2. [Установка зависимостей](#установка-зависимостей)
3. [Настройка базы данных](#настройка-базы-данных)
4. [Миграции](#миграции)
5. [Создание суперпользователя](#создание-суперпользователя)
6. [Запуск проекта](#запуск-проекта)
7. [Дополнительная настройка](#дополнительная-настройка)

## 🔧 Подготовка окружения

### Требования
- Python 3.10+
- PostgreSQL 14+ (или SQLite для разработки)
- pip
- virtualenv (рекомендуется)

### Создание виртуального окружения

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

## 📦 Установка зависимостей

```bash
pip install -r requirements.txt
```

Если возникают проблемы с установкой `psycopg2-binary`, попробуйте:

```bash
# Ubuntu/Debian
sudo apt-get install python3-dev libpq-dev

# macOS
brew install postgresql
```

## 🗄️ Настройка базы данных

### Вариант 1: SQLite (для разработки)

По умолчанию проект настроен на SQLite. Ничего дополнительно делать не нужно.

### Вариант 2: PostgreSQL (для продакшена)

1. Создайте базу данных:
```bash
sudo -u postgres psql
CREATE DATABASE uvp_db;
CREATE USER uvp_user WITH PASSWORD 'your_password';
ALTER ROLE uvp_user SET client_encoding TO 'utf8';
ALTER ROLE uvp_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE uvp_user SET timezone TO 'Europe/Kiev';
GRANT ALL PRIVILEGES ON DATABASE uvp_db TO uvp_user;
\q
```

2. Создайте файл `.env` в корне проекта:
```env
SECRET_KEY=your-super-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.postgresql
DB_NAME=uvp_db
DB_USER=uvp_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

## 🔄 Миграции

Примените миграции для создания таблиц в базе данных:

```bash
python manage.py makemigrations
python manage.py migrate
```

## 👤 Создание суперпользователя

```bash
python manage.py createsuperuser
```

Введите:
- Username (например: admin)
- Email
- Password (дважды)

## 🚀 Запуск проекта

### Режим разработки

```bash
python manage.py runserver
```

Проект будет доступен по адресу: http://127.0.0.1:8000

### Панель администратора

http://127.0.0.1:8000/admin

## ⚙️ Дополнительная настройка

### Сбор статических файлов (для продакшена)

```bash
python manage.py collectstatic --noinput
```

### Создание тестовых данных

```bash
# Создайте группы пользователей
python manage.py shell
```

```python
from apps.users.models import GroupUsers

GroupUsers.objects.create(name='admin')
GroupUsers.objects.create(name='manager')
GroupUsers.objects.create(name='guest')
```

### Загрузка фикстур (если есть)

```bash
python manage.py loaddata fixtures/initial_data.json
```

## 📁 Структура проекта

```
uvp_project/
├── apps/                       # Приложения
│   ├── users/                 # Пользователи и авторизация
│   ├── projects/              # Проекты
│   ├── tasks/                 # Задачи
│   ├── billing/               # Финансы
│   ├── access/                # Доступы
│   └── media_files/           # Медиафайлы
├── config/                     # Настройки Django
│   ├── settings.py            # Главный конфиг
│   ├── urls.py                # URL маршруты
│   └── wsgi.py                # WSGI точка входа
├── templates/                  # Jinja2 шаблоны
│   ├── base.html              # Базовый шаблон
│   ├── projects/              # Шаблоны проектов
│   ├── tasks/                 # Шаблоны задач
│   └── ...
├── static/                     # Статические файлы
│   ├── css/                   # Стили
│   ├── js/                    # JavaScript
│   │   └── rete-structure.js  # Rete.js для визуализации
│   └── img/                   # Изображения
├── media/                      # Загруженные файлы
├── manage.py                   # Django CLI
├── requirements.txt            # Зависимости
└── README.md                   # Документация
```

## 🔐 Безопасность

### Для продакшена обязательно:

1. Измените `SECRET_KEY` в `.env`
2. Установите `DEBUG=False`
3. Настройте `ALLOWED_HOSTS`
4. Используйте HTTPS
5. Настройте правильные права доступа к файлам
6. Регулярно обновляйте зависимости

## 🐳 Docker (опционально)

Если хотите использовать Docker, создайте `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

И `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: uvp_db
      POSTGRES_USER: uvp_user
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      - DB_ENGINE=django.db.backends.postgresql
      - DB_NAME=uvp_db
      - DB_USER=uvp_user
      - DB_PASSWORD=your_password
      - DB_HOST=db
      - DB_PORT=5432

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

Запуск:
```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
python manage.py test

# Запуск тестов конкретного приложения
python manage.py test apps.projects

# С подробным выводом
python manage.py test --verbosity=2
```

## 📊 Мониторинг и логи

Логи Django будут выводиться в консоль при запуске с `runserver`.

Для продакшена настройте логирование в `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/uvp/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## ❓ Решение проблем

### Ошибка "ModuleNotFoundError: No module named 'apps'"

```bash
# Убедитесь, что вы в корне проекта
pwd

# И что виртуальное окружение активировано
which python
```

### Ошибка подключения к базе данных

Проверьте настройки в `.env` и убедитесь, что PostgreSQL запущен:

```bash
sudo systemctl status postgresql
```

### Ошибки при миграциях

```bash
# Очистите все миграции и пересоздайте
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
python manage.py makemigrations
python manage.py migrate
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи Django
2. Убедитесь, что все зависимости установлены
3. Проверьте настройки в `.env`
4. Посмотрите документацию Django: https://docs.djangoproject.com/

## 📝 Дополнительные команды

```bash
# Создать приложение
python manage.py startapp app_name

# Открыть Django shell
python manage.py shell

# Проверить код на ошибки
python manage.py check

# Показать SQL миграций
python manage.py sqlmigrate app_name migration_name

# Создать дамп данных
python manage.py dumpdata > db_dump.json

# Загрузить дамп
python manage.py loaddata db_dump.json
```

Удачи с развёртыванием! 🚀
