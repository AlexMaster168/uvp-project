# API Documentation

## Overview
УВП provides a RESTful API for managing projects, tasks, billing, access credentials, and media files.

**Base URL:** `http://localhost:8000/api/`

**Authentication:** Session-based authentication (Django sessions)

## Authentication Endpoints

### Login
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

**Response:**
```json
{
  "detail": "Login successful"
}
```

### Logout
```
POST /api/auth/logout/
```

**Response:**
```json
{
  "detail": "Logout successful"
}
```

## Projects

### List Projects
```
GET /api/projects/
```

**Query Parameters:**
- `q` - Search by name or description
- `status` - Filter by status (planned, in_progress, idle, sleep, my)
- `start_date` - Filter by start date
- `end_date` - Filter by end date
- `ordering` - Sort by field (name, start_date, created_at)

**Response:**
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/projects/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Alpha Launch",
      "description": "Product launch project",
      "status": "in_progress",
      "start_date": "2025-01-01",
      "end_date": "2025-12-31",
      "logo": "http://localhost:8000/media/project_logos/logo.png",
      "creator_name": "admin",
      "tags": [
        {"id": 1, "name": "Web", "range": 0, "importance": 5}
      ],
      "tasks_count": 12,
      "financial_summary": {
        "income": 50000.00,
        "expense": 10000.00,
        "balance": 40000.00
      },
      "owners": [
        {"id": 1, "username": "admin"}
      ]
    }
  ]
}
```

### Get Project Details
```
GET /api/projects/{id}/
```

**Response:**
```json
{
  "id": 1,
  "name": "Alpha Launch",
  "description": "Product launch project",
  "status": "in_progress",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "logo": "http://localhost:8000/media/project_logos/logo.png",
  "u_creator": 1,
  "u_creator_name": "admin",
  "tags": [
    {"id": 1, "name": "Web", "range": 0, "importance": 5}
  ],
  "members": [
    {
      "id": 1,
      "user": 1,
      "user_name": "admin",
      "role": "owner"
    }
  ],
  "duration_days": 365,
  "structure_data": {},
  "created_at": "2025-02-01T10:00:00Z",
  "updated_at": "2025-02-01T10:00:00Z"
}
```

### Create Project
```
POST /api/projects/
```

**Request Body:**
```json
{
  "name": "New Project",
  "description": "Project description",
  "start_date": "2025-03-01",
  "end_date": "2025-12-31",
  "status": "planned",
  "u_tags": [1, 2]
}
```

**Response:** Same as Get Project Details

### Update Project
```
PATCH /api/projects/{id}/
```

**Request Body:** (partial update)
```json
{
  "status": "in_progress",
  "description": "Updated description"
}
```

### Delete Project
```
DELETE /api/projects/{id}/
```

**Response:** 204 No Content

### Get/Save Project Structure (Rete.js)
```
GET /api/projects/{id}/structure/
POST /api/projects/{id}/structure/
```

**POST Request Body:**
```json
{
  "nodes": [
    {
      "id": "task_1",
      "type": "tasks",
      "title": "Design mockups",
      "status": "in_progress",
      "x": 100,
      "y": 200
    }
  ],
  "connections": [
    {
      "from": "project",
      "to": "task_1"
    }
  ]
}
```

## Tasks

### List Tasks
```
GET /api/tasks/
```

**Query Parameters:**
- `project` - Filter by project ID
- `status` - Filter by status (todo, in_progress, done)
- `search` - Search in title

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "title": "Design homepage",
      "status": "in_progress",
      "estimated_time": 20.0,
      "actual_time": 15.5,
      "project": 1,
      "project_name": "Alpha Launch",
      "assignees": [
        {"id": 2, "username": "designer"}
      ],
      "tags": [
        {"id": 3, "name": "Design"}
      ],
      "created_at": "2025-02-01T10:00:00Z",
      "updated_at": "2025-02-01T12:00:00Z"
    }
  ]
}
```

### Create Task
```
POST /api/tasks/
```

**Request Body:**
```json
{
  "title": "Write documentation",
  "status": "todo",
  "estimated_time": 10.0,
  "actual_time": 0.0,
  "project": 1,
  "u_users": [2, 3],
  "u_tags": [4]
}
```

### Update Task
```
PATCH /api/tasks/{id}/
```

**Request Body:**
```json
{
  "status": "done",
  "actual_time": 8.5
}
```

## Tags

### List Tags
```
GET /api/tags/
```

**Query Parameters:**
- `search` - Search by name

**Response:**
```json
[
  {
    "id": 1,
    "name": "Web",
    "range": 0,
    "importance": 5
  }
]
```

### Create Tag
```
POST /api/tags/
```

**Request Body:**
```json
{
  "name": "Backend",
  "range": 0,
  "importance": 3
}
```

## Users

### List Users
```
GET /api/users/
```

**Query Parameters:**
- `q` - Search by username or email
- `group` - Filter by group name

**Response:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "u_group": 1,
    "u_group_name": "Admin",
    "status": "active",
    "is_staff": true,
    "is_active": true
  }
]
```

### Create User
```
POST /api/users/
```

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "u_group": 2
}
```

## Billing

### List Billing Entries
```
GET /api/billing/
```

**Query Parameters:**
- `project` - Filter by project ID
- `operation` - Filter by operation type (income, expense)
- `tag` - Filter by tag
- `date` - Filter by date

**Response:**
```json
[
  {
    "id": 1,
    "project": 1,
    "project_name": "Alpha Launch",
    "date": "2025-02-01",
    "amount": "1500.00",
    "description": "Initial investment",
    "tag": "actual_income",
    "operation": "income",
    "participants": [
      {"id": 1, "username": "investor"}
    ],
    "created_at": "2025-02-01T10:00:00Z",
    "updated_at": "2025-02-01T10:00:00Z"
  }
]
```

### Create Billing Entry
```
POST /api/billing/
```

**Request Body:**
```json
{
  "project": 1,
  "date": "2025-02-05",
  "amount": "450.00",
  "description": "Design services",
  "tag": "approved_expense",
  "operation": "expense",
  "users": [2]
}
```

## Access

### List Access Credentials
```
GET /api/access/
```

**Query Parameters:**
- `project` - Filter by project ID
- `search` - Search in login, url, description

**Response:**
```json
[
  {
    "id": 1,
    "project": 1,
    "project_name": "Alpha Launch",
    "url": "https://github.com/example/repo",
    "url_drive": "",
    "login": "dev_team",
    "password_masked": "••••••••",
    "description": "GitHub repository access",
    "registration_date": "2025-01-01",
    "update_date": null,
    "change_comment": "",
    "amount": null,
    "tags": ["dev"],
    "created_at": "2025-02-01T10:00:00Z",
    "updated_at": "2025-02-01T10:00:00Z"
  }
]
```

**Note:** Password is write-only. Use `password_masked` for display.

### Create Access Entry
```
POST /api/access/
```

**Request Body:**
```json
{
  "project": 1,
  "url": "https://aws.amazon.com",
  "login": "admin@company.com",
  "password": "actual_password_here",
  "description": "AWS Console Access",
  "amount": "50.00",
  "tags": ["hosting", "critical"]
}
```

## Media Files

### List Media Files
```
GET /api/media/
```

**Query Parameters:**
- `project` - Filter by project ID

**Response:**
```json
[
  {
    "id": 1,
    "file": "http://localhost:8000/media/project_media/screenshot.png",
    "uploaded_at": "2025-02-01T10:00:00Z",
    "description": "Homepage screenshot",
    "project": 1,
    "project_name": "Alpha Launch",
    "is_image": true,
    "is_video": false,
    "is_pdf": false
  }
]
```

### Upload Media File
```
POST /api/media/
```

**Request:** multipart/form-data

**Form Data:**
- `file` - File to upload
- `project` - Project ID
- `description` - File description

## Error Responses

### 400 Bad Request
```json
{
  "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

## Rate Limiting

Currently, there are no rate limits in the development environment. For production, implement rate limiting using Django REST Framework throttling.

## Pagination

Default page size: 20 items

To change page size:
```
GET /api/projects/?page_size=50
```

## Filtering and Searching

Most list endpoints support:
- **Filtering:** Use query parameters matching field names
- **Search:** Use `?search=query` parameter
- **Ordering:** Use `?ordering=field_name` or `?ordering=-field_name` (descending)

## CORS

CORS is enabled for development. Configure `CORS_ALLOWED_ORIGINS` in `.env` for production.
