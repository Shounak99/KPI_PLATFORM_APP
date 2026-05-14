# KPI Platform

A Django web app for tracking KPIs across projects with role-based access control.

## Requirements

- Python 3.10+
- Docker Desktop (for PostgreSQL)

## Local Setup

### 1. Clone and create virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start PostgreSQL via Docker

```bash
docker run --name kpi-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=kpi_platform -p 5433:5432 -d postgres
```

> Note: uses port 5433 to avoid conflict with any local PostgreSQL installation.

### 4. Configure environment

Create a `.env` file in the project root:

```
SECRET_KEY=django-insecure-dev-key-change-in-production-abc123xyz
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=kpi_platform
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5433
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (admin access)

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

App runs at `http://localhost:8000`

---

## User Roles

| Role | Permissions |
|------|-------------|
| Admin | Full access — manage all projects and KPIs |
| Project Owner | Create projects, manage own projects and KPIs only |
| Viewer | Read-only access to all projects and KPI summaries |

Assign roles at registration or via Django admin at `/admin/`.

---

## Business Decisions & Assumptions

**KPI Status**
- Status is manually set by the user (On Track / At Risk / Off Track)
- System provides a suggested status based on math (`suggested_status` property) but does not auto-apply it
- Thresholds: ≥90% of target = On Track, 70–89% = At Risk, <70% = Off Track

**Overall Project Status**
- Worst case wins — one Off Track KPI makes the whole project Off Track
- All On Track → project is On Track
- Project with zero KPIs has status "No KPIs"

**KPI Design**
- KPIs are not hardcoded — each project can have any number with any name
- `unit` is free text (%, $, score, etc.)
- `actual_value` defaults to 0 on creation

**Data Integrity**
- Deleting a project cascades — all its KPIs are deleted automatically
- `target_value` and `actual_value` must be ≥ 0

**Progress Calculation**
- `progress_percent` caps at 100% even if actual exceeds target
- Stored as decimal — allows values like 87.5%

**Project is Live**
project url- https://kpiplatformapp-production.up.railway.app/
