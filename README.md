# KPI Platform

A full-stack KPI tracking application with a Django REST API backend and React frontend. Supports role-based access control, JWT authentication, and KPI health monitoring across projects.

## Live URLs

- **Frontend (React):** https://kpi-platform-app.vercel.app
- **Backend API (Django):** https://kpiplatformapp-production.up.railway.app/api/
- **Django Admin:** https://kpiplatformapp-production.up.railway.app/admin/

---

## Architecture

```
React (Vercel) → Django REST API (Railway) → PostgreSQL (Railway)
```

- Frontend and backend are fully decoupled
- All FE↔BE communication via REST API with JWT authentication

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + Bootstrap 5 |
| Backend | Django 5.2 + Django REST Framework |
| Auth | JWT (djangorestframework-simplejwt) |
| Database | PostgreSQL |
| Frontend Hosting | Vercel |
| Backend Hosting | Railway |

---

## User Roles

| Role | Permissions |
|------|-------------|
| Admin | Full access — manage all projects and KPIs |
| Project Owner | Create projects, manage own projects and KPIs only |
| Viewer | Read-only access to all projects and KPI summaries |

Assign roles at registration or via Django admin.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/login/` | Login, returns JWT tokens |
| POST | `/api/auth/refresh/` | Refresh access token |
| GET | `/api/auth/me/` | Get current user info |
| GET/POST | `/api/projects/` | List / create projects |
| GET/PUT/DELETE | `/api/projects/<id>/` | Retrieve / update / delete project |
| GET/POST | `/api/projects/<id>/kpis/` | List / create KPIs |
| GET/PUT/DELETE | `/api/projects/<id>/kpis/<id>/` | Retrieve / update / delete KPI |

---

## Local Setup

Two ways to run locally: **Docker** (recommended, one command) or **manual** (separate backend + frontend setup).

---

### Option 1: Docker (Recommended)

Runs the full stack — PostgreSQL, Django backend, and React frontend — in containers.

**Prerequisites:** Docker Desktop

**1. Clone the repo**
```bash
git clone https://github.com/Shounak99/KPI_PLATFORM_APP.git
cd KPI_PLATFORM_APP
```

**2. Start all services**
```bash
docker compose up --build
```

First run builds the images (~2–3 min). Subsequent runs are faster.

| Service | URL |
|---------|-----|
| Frontend (React) | http://localhost:3000 |
| Backend API | http://localhost:8000/api |
| Django Admin | http://localhost:8000/admin |

**3. Seed dummy data (optional — 20 projects, 60 KPIs)**
```bash
docker compose exec backend python manage.py seed_data
```

**4. Create a superuser (for Django admin)**
```bash
docker compose exec backend python manage.py createsuperuser
```

**5. Stop all services**
```bash
docker compose down
```

To also delete the database volume:
```bash
docker compose down -v
```

---

### Option 2: Manual Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker Desktop (for PostgreSQL)

### Backend Setup (Manual)

**1. Clone and create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Start PostgreSQL via Docker**
```bash
docker run --name kpi-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=kpi_platform -p 5433:5432 -d postgres
```

> Note: uses port 5433 to avoid conflict with any local PostgreSQL installation.

**4. Configure environment — create `.env` in project root:**
```
SECRET_KEY=django-insecure-dev-key-change-in-production-abc123xyz
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=kpi_platform
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5433

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

**5. Run migrations**
```bash
python manage.py migrate
```

**6. Seed dummy data (optional — creates 20 projects, 60 KPIs)**
```bash
python manage.py seed_data
```

**7. Create superuser**
```bash
python manage.py createsuperuser
```

**8. Run backend server**
```bash
python manage.py runserver
```

Backend runs at `http://localhost:8000`

---

### Frontend Setup (Manual)

**1. Install dependencies**
```bash
cd frontend
npm install
```

**2. Configure environment — create `frontend/.env.local`:**
```
VITE_API_BASE_URL=http://localhost:8000/api
```

**3. Run frontend dev server**
```bash
npm run dev
```

Frontend runs at `http://localhost:5173`

---

## Deployment

### Backend (Railway)
- Connects to GitHub repo — auto-deploys on push
- Set environment variables in Railway dashboard:
  - `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`
  - `DATABASE_URL` (auto-set by Railway Postgres)
  - `CORS_ALLOWED_ORIGINS=https://your-vercel-url.vercel.app`

### Frontend (Vercel)
- Deploy `frontend/` folder to Vercel
- Set environment variable:
  - `VITE_API_BASE_URL=https://kpiplatformapp-production.up.railway.app/api`

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
