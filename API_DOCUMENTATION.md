# API Documentation

## Overview
УВП provides a RESTful API for managing projects, tasks, billing, access credentials, media files, and users.

**Base URL:** `http://localhost:8000/api/`

**Authentication:** Session-based authentication & Google OAuth.

## Authentication Endpoints

### Standard Login (Session)

`POST /api/auth/login/`

**Request Body:**
```json
{
  "username": "admin",
  "password": "password123"
}

```

### Google OAuth Login

`GET /accounts/google/login/`

### Logout

`POST /api/auth/logout/`

## Projects

### List Projects

`GET /api/projects/`

**Query Parameters:**

* `q`: Search by project name
* `status`: Filter by status (planned, in_progress, idle, sleep, finished)
* `owner`: Filter by owner ID
* `start_date`: Filter by start date
* `end_date`: Filter by end date
* `ordering`: Sort results

### Create Project

`POST /api/projects/`

**Request Body:**

```json
{
  "name": "New Project",
  "description": "Detailed project description",
  "status": "planned",
  "start_date": "2026-03-10",
  "end_date": "2026-12-31"
}

```

### Get Project Details

`GET /api/projects/{id}/`

### Update Project

`PUT /api/projects/{id}/`
`PATCH /api/projects/{id}/`

### Delete Project

`DELETE /api/projects/{id}/`

## Tasks & Subtasks

### List Tasks

`GET /api/tasks/`

**Query Parameters:**

* `project`: Filter by project ID
* `status`: Filter by status (todo, in_progress, done)
* `assignee`: Filter by user ID

### Create Task

`POST /api/tasks/`

**Request Body:**

```json
{
  "title": "Backend Development",
  "description": "Setup the database and initial models",
  "project": 1,
  "assignee": 2,
  "status": "todo",
  "plan_hours": 20.0,
  "fact_hours": 0.0
}

```

### Get Task Details

`GET /api/tasks/{id}/`

### Update Task

`PUT /api/tasks/{id}/`
`PATCH /api/tasks/{id}/`

### Delete Task

`DELETE /api/tasks/{id}/`

### List Subtasks

`GET /api/subtasks/`

### Create Subtask

`POST /api/subtasks/`

**Request Body:**

```json
{
  "parent_task": 1,
  "title": "Create User model",
  "status": "todo",
  "plan_hours": 5.0
}

```

### Delete Subtask

`DELETE /api/subtasks/{id}/`

## Access Credentials

### List Access

`GET /api/access/`

### Create Access

`POST /api/access/`

**Request Body:**

```json
{
  "project": 1,
  "service_name": "Production Database",
  "url": "[https://db.example.com](https://db.example.com)",
  "login": "db_admin",
  "password": "securepassword123"
}

```

### Get Access Details

`GET /api/access/{id}/`

### Update Access

`PUT /api/access/{id}/`
`PATCH /api/access/{id}/`

### Delete Access

`DELETE /api/access/{id}/`

## Billing

### List Transactions

`GET /api/billing/`

**Query Parameters:**

* `project`: Filter by project ID
* `operation`: Filter by operation type (income, expense)

### Create Transaction

`POST /api/billing/`

**Request Body:**

```json
{
  "project": 1,
  "operation": "income",
  "amount": 2500.00,
  "date": "2026-03-10",
  "description": "Initial advance payment"
}

```

### Get Transaction Details

`GET /api/billing/{id}/`

### Update Transaction

`PUT /api/billing/{id}/`
`PATCH /api/billing/{id}/`

### Delete Transaction

`DELETE /api/billing/{id}/`

## Media Files

### List Media Files

`GET /api/media_files/`

**Query Parameters:**

* `project`: Filter by project ID

### Upload File

`POST /api/media_files/`

**Content-Type:** `multipart/form-data`

**Form Data:**

* `project`: 1
* `file`: (binary file data)
* `title`: "Project Architecture Diagram"
* `description`: "Visual representation of the system architecture"

### Get Media File Details

`GET /api/media_files/{id}/`

### Delete Media File

`DELETE /api/media_files/{id}/`

## Users

### List Users

`GET /api/users/`

### Get User Details

`GET /api/users/{id}/`

### Get Current User Profile

`GET /api/users/profile/`

```

```