### 3. `API_DOCUMENTATION.md`

Обновлен раздел аутентификации.

```markdown
# API Documentation

## Overview
УВП provides a RESTful API for managing projects, tasks, billing, access credentials, and media files.

**Base URL:** `http://localhost:8000/api/`
**Authentication:** Session-based authentication & Google OAuth.

## Authentication Endpoints

### Standard Login (Session)

```

POST /api/auth/login/

```
**Request Body:**
```json
{
  "username": "admin",
  "password": "password123"
}

```

### Google OAuth Login

Для входа через Google используется стандартный механизм перенаправления `django-allauth`.
**Browser URL:** `/accounts/google/login/`

### Logout

```
POST /api/auth/logout/

```

## Projects

### List Projects

```
GET /api/projects/

```

**Query Parameters:** `q`, `status`, `start_date`, `end_date`, `ordering`

### Get Project Details

```
GET /api/projects/{id}/

```

Returns project data including calculated `financial_summary`, `tasks_count` and `structure_data` (Rete.js JSON).

## Tasks & Subtasks

### List Tasks

```
GET /api/tasks/

```

### List Subtasks

```
GET /api/subtasks/

```

## Access Credentials

### List Access

```
GET /api/access/

```

**Note:** The `password` field is write-only. The response contains `password_masked` (e.g., "••••••••").

## Billing

### List Transactions

```
GET /api/billing/

```

Supports filtering by `operation` (income/expense) and `project`.

## Media Files

### Upload File

```
POST /api/media_files/

```

**Content-Type:** `multipart/form-data`

```

```