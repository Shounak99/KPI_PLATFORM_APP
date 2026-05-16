# DECISIONS.md

## Overall Architecture Rationale

Built as a decoupled full-stack application:

- **Backend:** Django REST Framework — pure API, no HTML rendering
- **Frontend:** React (Vite) — calls the API, handles all UI rendering
- **Communication:** REST API with JWT authentication

This architecture was chosen because:
- Clean separation of concerns — frontend and backend can be developed, deployed, and scaled independently
- REST API makes the backend reusable — mobile apps, third-party integrations, or a different frontend can consume the same API without changes
- Industry-standard pattern for modern web applications

Four Django apps separate domain concerns:
- `projects` — Project model, CRUD API views, serializers
- `kpis` — KPI model, CRUD API views, serializers
- `accounts` — Custom User model, JWT auth views (register, login, me)
- `api` — Central URL routing for all API endpoints

---

## Data Model Design

```
CustomUser
    └── Project (owner FK)
            └── KPI (project FK)
```

- `CustomUser` extends Django's `AbstractUser` — adds a `role` field without rewriting auth from scratch
- `Project` owns `KPIs` via ForeignKey with `CASCADE` delete — no orphan KPIs possible
- `KPI` stores both `target_value` and `actual_value` as `DecimalField` — avoids floating point precision errors on financial or percentage data
- `status` is a manual CharField with choices — user has final say on status, not the system

---

## KPI Flexibility Approach

KPIs are intentionally generic:

- `name` is free text — any metric can be tracked (revenue, NPS, uptime, units sold)
- `unit` is free text — not an enum (%, $, score, days, etc.) — avoids the need to predict all measurement types upfront
- `target_value` and `actual_value` are decimals — works for whole numbers, percentages, and currency
- No hardcoded KPI types — each project defines its own KPIs

The `suggested_status` property computes a recommendation (≥90% = On Track, 70–89% = At Risk, <70% = Off Track) but does not auto-apply it. The user retains final control. This avoids the system overriding human judgment on context it cannot know (e.g. a KPI at 65% but ahead of schedule).

---

## Scalability Considerations

**N+1 problem in API serializer:**
`ProjectSerializer` runs 3 separate DB queries per project to count KPI statuses (`on_track`, `at_risk`, `off_track`). At 50 projects this is 150+ extra queries per API call.

**Known fix (not yet implemented):**
Replace serializer method fields with a single annotated query in the viewset:
```python
Project.objects.annotate(
    on_track=Count('kpis', filter=Q(kpis__status='on_track')),
    at_risk=Count('kpis', filter=Q(kpis__status='at_risk')),
    off_track=Count('kpis', filter=Q(kpis__status='off_track')),
)
```
This reduces queries from O(n) to O(1) regardless of project count.

**Server-side pagination implemented** — DRF `PageNumberPagination` with `PAGE_SIZE=10` applied globally. API returns `{count, next, previous, results}` envelope on all list endpoints.

**ProjectList uses true server-side pagination** — page state drives `?page=N` query param; `count` from response computes total pages; no client-side slicing.

**KpiTable uses client-side search/filter/pagination over fully-fetched dataset** — `fetchAllPages` helper chases `next` links until exhausted, collecting all projects and all KPIs across pages. Client-side search, status filter, and 10-row pagination then operate on the full in-memory set. Trade-off: more API calls on load (O(projects) requests), but avoids needing a dedicated cross-project KPI search endpoint.

**ProjectDetail fetches all KPI pages** — loops `next` links to collect all KPIs for a project regardless of count. Prevents truncation on projects with >10 KPIs.

**No caching** — Redis cache would significantly reduce DB load on high-traffic deployments.

---

## Performance Considerations

- Static files served via `WhiteNoise` — no separate CDN or nginx needed at this scale
- `DecimalField` over `FloatField` for KPI values — slight performance cost but avoids floating point bugs on financial data
- No background tasks — all operations are synchronous. Celery + Redis would be needed for bulk imports or scheduled reports
- DB connection pooling not configured — `CONN_MAX_AGE` or `pgbouncer` would help at scale

---

## Authentication and Role Design

**JWT Authentication:**
`djangorestframework-simplejwt` issues short-lived access tokens (60 min) and long-lived refresh tokens (7 days). Chosen over Django session auth because:
- Sessions don't work cross-origin (React on Vercel, Django on Railway)
- JWT is stateless — no server-side session storage needed
- Standard for decoupled frontend/backend architectures

**Custom User Model:**
Django strongly recommends creating a custom user model at project start. `AbstractUser` was chosen — keeps all default Django auth behaviour and only adds the `role` field.

**Three roles:**

| Role | Can do |
|------|--------|
| Admin | Full access — all projects and KPIs |
| Project Owner | Create projects, manage only own projects and KPIs |
| Viewer | Read-only access to all projects and KPI summaries |

Role checks happen in DRF views via `raise PermissionDenied` — server-side enforcement. React UI hides buttons based on role stored in `localStorage` — cosmetic only. The real guard is always the API.

**Token storage:** JWT tokens stored in `localStorage`. Known security tradeoff — vulnerable to XSS attacks. `httpOnly` cookies would be more secure but require additional CSRF handling. Acceptable for this scope.

---

## Assumptions Around Authentication and Roles

- **Self-selected roles** — users pick their own role at registration. No admin approval step or invite system. Known security gap: anyone can register as Admin. Acceptable for internal tools with trusted users.
- **No email verification** — accounts are active immediately after registration.
- **No password reset** — admin must reset via Django admin (`/admin/`). Full email-based reset flow not implemented.
- **No multi-tenancy** — all data is visible based on role, not organisation. Adding tenancy would require an `Organisation` model and filtering every query by org.
- **No token refresh on expiry** — access token expires after 60 min. User must log in again. Automatic refresh via interceptor not implemented.

---

## Trade-offs Made During Implementation

| Decision | Trade-off |
|----------|-----------|
| Decoupled React + Django REST API | Clean separation, industry standard — but more complex than a monolith |
| JWT in localStorage | Simple implementation — but vulnerable to XSS vs httpOnly cookies |
| Self-selected roles at registration | Simple UX — but anyone can claim Admin role |
| Server-side pagination (ProjectList) | Correct — only fetches current page. KpiTable still fetches all for cross-project search |
| N+1 in serializer for KPI counts | Readable code — causes extra queries at scale |
| Hardcoded role thresholds (90/70%) | Simple and transparent — but not configurable per project |
| `DecimalField` for values | Precision over performance — slightly slower than `FloatField` |
| Seed data via management command | Easy demo setup — but manual step, not automated |

---

## Shortcuts Taken Due to Exercise Timeline

- **No email verification on registration** — would require an email backend (SendGrid, SES) and token flow
- **No password reset flow** — skipped in favour of admin-managed resets via `/admin/`
- **No JWT refresh interceptor** — token expires after 60 min, user must re-login manually
- **KpiTable fetches all records despite server-side pagination** — display is paginated (10 rows, search, status filter), but all data must be fetched first for cross-project search to work; a dedicated `/api/kpis/` endpoint with server-side search/filter would be the correct fix
- **N+1 queries in serializer** — `SerializerMethodField` for KPI counts runs separate queries; `annotate()` fix identified but not implemented
- **No test suite** — no unit or integration tests written; all testing done manually
- **No rate limiting on auth endpoints** — brute force attacks on login not prevented
- **Role-based access in React UI is cosmetic** — buttons hidden via `localStorage` role check; server-side API is the real enforcement layer
- **Seed data not auto-deployed** — must be run manually via Railway shell or pre-deploy step
