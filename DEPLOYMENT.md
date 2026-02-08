### 1. `DEPLOYMENT.md`

Добавлен раздел по настройке Google Cloud и переменных окружения.

```markdown
# Полная инструкция по развёртыванию УВП

## 📋 Оглавление
1. [Подготовка окружения](#подготовка-окружения)
2. [Установка зависимостей](#установка-зависимостей)
3. [Настройка базы данных](#настройка-базы-данных)
4. [Настройка Google OAuth](#настройка-google-oauth)
5. [Миграции](#миграции)
6. [Создание суперпользователя](#создание-суперпользователя)
7. [Запуск проекта](#запуск-проекта)
8. [Docker](#docker-опционально)

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

## 🗄️ Настройка базы данных и ENV

1. Создайте базу данных (для PostgreSQL):

```sql
CREATE DATABASE uvp_db;
CREATE USER uvp_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE uvp_db TO uvp_user;

```

2. Создайте файл `.env` в корне проекта:

```env
SECRET_KEY=your-super-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=uvp_db
DB_USER=uvp_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Google OAuth
GOOGLE_CLIENT_ID=ваш_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=ваш_client_secret

```

## 🔐 Настройка Google OAuth

Для работы входа через Google необходимо выполнить настройку в Google Cloud Console:

1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com/).
2. Создайте **OAuth 2.0 Client ID** (Web application).
3. Добавьте **Authorized redirect URIs**:
* Локально: `http://127.0.0.1:8000/accounts/google/login/callback/`
* Продакшн: `https://your-domain.com/accounts/google/login/callback/`


4. Скопируйте `Client ID` и `Client Secret` в файл `.env`.

**Важно:** После первого запуска зайдите в админ-панель (`/admin/`), перейдите в раздел **Sites** и измените домен `example.com` на `127.0.0.1:8000` (или ваш боевой домен).

## 🔄 Миграции

```bash
python manage.py makemigrations
python manage.py migrate

```

## 👤 Создание суперпользователя

```bash
python manage.py createsuperuser

```

## 🚀 Запуск проекта

```bash
python manage.py runserver

```

Проект будет доступен по адресу: `http://127.0.0.1:8000`

## 🐳 Docker (опционально)

Сборка и запуск контейнеров:

```bash
docker-compose up -d --build

```

Применение миграций внутри Docker:

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

```