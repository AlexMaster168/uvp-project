# Архитектура проекта УВП

## Обзор

УВП (Управление Временем Проектов) построен на основе Django с использованием модульной архитектуры приложений. Проект следует паттерну MVT (Model-View-Template) с дополнительным REST API слоем.

## Структура приложений

### 1. Users (apps/users/)
**Назначение:** Управление пользователями, аутентификация и авторизация

**Модели:**
- `GroupUsers` - группы пользователей (admin, manager, guest)
- `User` - расширенная модель пользователя Django

**Ключевые features:**
- Кастомная модель пользователя с группами
- Методы проверки ролей (is_super_admin, is_admin, etc.)
- Блокировка/разблокировка аккаунтов
- API для создания пользователей (только для админов)

### 2. Projects (apps/projects/)
**Назначение:** Управление проектами и связанными сущностями

**Модели:**
- `Tag` - теги для категоризации
- `Project` - основная модель проекта
- `ProjectMembership` - связь пользователей с проектами и их роли
- `Plan` - элементы плана проекта (связь задач с проектом в порядке)

**Ключевые features:**
- Хранение структуры проекта для Rete.js (JSON поле)
- Расчёт финансовых итогов
- M2M связи с тегами и владельцами
- Загрузка логотипов

### 3. Tasks (apps/tasks/)
**Назначение:** Управление задачами проекта

**Модели:**
- `Task` - задача с статусом, временем и исполнителями

**Ключевые features:**
- Множественные исполнители (M2M с User)
- Теги задач
- Отслеживание планируемого и фактического времени
- Статусы: todo, in_progress, done

### 4. Billing (apps/billing/)
**Назначение:** Финансовый учёт по проектам

**Модели:**
- `Billing` - финансовая операция

**Ключевые features:**
- Доходы и расходы
- Категории операций (planned_expense, actual_income, etc.)
- Множественные участники операции
- Автоматический расчёт балансов

### 5. Access (apps/access/)
**Назначение:** Хранение доступов к внешним ресурсам

**Модели:**
- `Access` - учётные данные и доступы

**Ключевые features:**
- Хранение URL, логинов и паролей
- Маскирование паролей в API
- Теги для категоризации (critical, hosting, etc.)
- Отслеживание стоимости подписок

### 6. MediaFiles (apps/media_files/)
**Назначение:** Управление медиафайлами проекта

**Модели:**
- `MediaFile` - загруженный файл

**Ключевые features:**
- Загрузка различных типов файлов
- Определение типа файла (image, video, pdf)
- Привязка к проекту

## Слои архитектуры

### Models (Модели данных)
Находятся в `apps/*/models.py`

- Определяют структуру БД
- Содержат бизнес-логику на уровне модели
- Используют Django ORM

### Serializers (Сериализаторы)
Находятся в `apps/*/serializers.py`

- Преобразуют модели в JSON и обратно
- Валидация данных на входе
- Настройка полей для разных действий (list, detail, create)

### Views (Представления)
Находятся в `apps/*/views.py`

**Web Views (Class-Based Views):**
- ListView - списки объектов
- DetailView - детальный просмотр
- CreateView/UpdateView - формы создания/редактирования

**API Views (DRF ViewSets):**
- ViewSet - полный CRUD через REST API
- Custom actions (@action decorator)
- Фильтрация, поиск, сортировка

### Permissions (Права доступа)
Находятся в `apps/*/permissions.py`

- `IsSuperAdminOrAdmin` - доступ только админам
- `IsProjectMember` - проверка членства в проекте
- `IsProjectOwnerOrManager` - проверка роли в проекте

### Templates (Шаблоны)
Находятся в `templates/`

**Используемая технология:** Jinja2

**Структура:**
- `base.html` - базовый шаблон с навигацией
- `*/list.html` - списки объектов
- `*/detail.html` - детальный просмотр
- `*/form.html` - формы создания/редактирования
- `structure.html` - специальная страница для Rete.js

### URLs (Маршруты)
- `config/urls.py` - главный роутер
- `apps/*/urls.py` - web-страницы приложения
- `apps/*/api_urls.py` - REST API endpoints

## Технологии и библиотеки

### Backend
- **Django 5.x** - основной фреймворк
- **Django REST Framework** - REST API
- **django-filter** - фильтрация в API
- **Pillow** - обработка изображений
- **psycopg2** - PostgreSQL драйвер
- **python-decouple** - управление переменными окружения

### Frontend
- **Jinja2** - шаблонизатор (вместо DTL)
- **Bootstrap 5** - CSS фреймворк
- **HTMX** - динамические обновления без JS
- **Alpine.js** - легковесный JS фреймворк
- **Rete.js** - визуализация графов

### Хранилище
- **SQLite** - для разработки
- **PostgreSQL** - для продакшена
- **File System / S3** - для медиа

## Паттерны и best practices

### 1. Separation of Concerns
- Модели содержат только бизнес-логику данных
- Представления отвечают за HTTP логику
- Сериализаторы - за преобразование данных
- Permissions - за проверку прав

### 2. DRY (Don't Repeat Yourself)
- Базовые permissions используются повторно
- Общие миксины для views
- Наследование сериализаторов

### 3. RESTful API Design
- CRUD операции через стандартные HTTP методы
- Использование статус-кодов
- Пагинация по умолчанию
- Фильтрация и поиск через query params

### 4. Security
- CSRF защита
- Permission classes на всех endpoints
- Маскирование паролей
- Hash паролей пользователей

## Модель данных

### Основные связи

```
User 1--* Project (creator)
User *--* Project (через ProjectMembership с ролью)
Project 1--* Task
Project 1--* Billing
Project 1--* Access
Project 1--* MediaFile
Task *--* User (assignees)
Project *--* Tag
Task *--* Tag
```

### Каскадное удаление

- При удалении проекта удаляются: задачи, billing, access, media
- При удалении пользователя: creator защищён (PROTECT)
- ProjectMembership удаляется вместе с проектом/пользователем

## API Architecture

### Аутентификация
Session-based (Django sessions)

### Endpoints Structure
```
/api/
  /auth/
    /login/
    /logout/
  /users/
  /projects/
    /{id}/
    /{id}/structure/
  /tasks/
  /tags/
  /billing/
  /access/
  /media/
```

### Response Format
```json
{
  "count": 100,
  "next": "url",
  "previous": "url",
  "results": [...]
}
```

## Frontend Architecture

### Jinja2 Templates
- Компонентная структура
- Переиспользуемый base.html
- Блоки для кастомизации (title, content, extra_js, etc.)

### HTMX Integration
- Динамическая загрузка контента без перезагрузки страницы
- Используется для модалок, фильтров
- hx-get, hx-post для асинхронных запросов

### Alpine.js
- Реактивные компоненты на стороне клиента
- Управление состоянием UI
- Используется для форм и интерактивных элементов

### Rete.js Integration
- Отдельная страница для визуализации
- Сохранение структуры в JSON
- Drag-and-drop интерфейс

## Deployment Architecture

### Development
```
Django Dev Server (runserver)
  ↓
SQLite Database
  ↓
Local File System (media)
```

### Production
```
Nginx (Reverse Proxy)
  ↓
Gunicorn (WSGI Server)
  ↓
Django Application
  ↓
PostgreSQL Database
  ↓
S3/MinIO (Media Storage)
```

## Масштабирование

### Горизонтальное
- Несколько Gunicorn workers
- Load balancer перед Nginx
- Redis для кеша сессий

### Вертикальное
- Оптимизация запросов (select_related, prefetch_related)
- Database indexes на часто используемых полях
- Кеширование тяжёлых вычислений

### Database
- Master-Slave репликация PostgreSQL
- Read replicas для отчётов
- Партиционирование больших таблиц

## Мониторинг и логирование

### Логи
- Django request/response logs
- Error tracking
- Audit logs для важных операций

### Метрики
- Request response time
- Database query time
- API endpoint usage
- User activity

## Безопасность

### На уровне приложения
- CSRF tokens
- XSS protection
- SQL injection protection (ORM)
- Rate limiting (опционально)

### На уровне инфраструктуры
- HTTPS only
- Secure headers
- Database credentials в environment variables
- Регулярные backup'ы

## Будущие улучшения

1. **Кеширование**
   - Redis для сессий
   - Cache для часто запрашиваемых данных

2. **Асинхронные задачи**
   - Celery для тяжёлых операций
   - Email notifications
   - Отчёты

3. **Real-time updates**
   - WebSockets для обновлений структуры
   - Notifications

4. **Расширенная аналитика**
   - Dashboard с графиками
   - Экспорт отчётов

5. **Интеграции**
   - Calendar sync (Google Calendar, Outlook)
   - Git integration
   - Slack notifications

## Заключение

Архитектура УВП спроектирована с учётом:
- Модульности и расширяемости
- Безопасности
- Производительности
- Простоты поддержки

Проект готов к развёртыванию и дальнейшему развитию.
