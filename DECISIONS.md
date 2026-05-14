# DECISIONS.md

## Overall Architecture Rationale

Built as a Django monolith — single codebase serving both backend logic and HTML templates via Django's template engine. Chosen over a REST API + frontend framework split because:

- MVP scope does not justify the complexity of two separate codebases
- Django's ORM, admin, auth, and forms provide everything needed out of the box
- Faster to build, easier to deploy as a single unit

Two Django apps (`projects`, `kpis`) separate domain concerns. A third app (`accounts`) handles authentication. This keeps models, views, and templates scoped per domain rather than dumped into one giant app.

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

**Current approach (N+1 problem):**
The `kpi_summary` property on `Project` runs 5 separate DB queries per project on the list page. At 50 projects this is 250+ queries — acceptable for MVP, not for production scale.

**Known fix (not yet implemented):**
Replace with a single annotated query:
```python
Project.objects.annotate(
    total_kpis=Count('kpis'),
    on_track=Count('kpis', filter=Q(kpis__status='on_track')),
    at_risk=Count('kpis', filter=Q(kpis__status='at_risk')),
    off_track=Count('kpis', filter=Q(kpis__status='off_track')),
)
```
This reduces list page queries from O(n) to O(1) regardless of project count.

**No pagination implemented** — a list of 1000 projects would load slowly. Django's `Paginator` class would fix this with minimal changes.

**No caching** — repeated visits to the project list re-query the DB every time. Django's cache framework with Redis would reduce DB load significantly.

---

## Performance Considerations

- Static files served via `WhiteNoise` — avoids needing a separate CDN or nginx for static assets at this scale
- `DecimalField` over `FloatField` for KPI values — slight performance cost but avoids floating point bugs on financial data
- No background tasks — all operations are synchronous request/response. For future features like bulk KPI imports or scheduled reports, Celery + Redis would be needed
- DB connection pooling not configured — Django opens a new connection per request by default. At scale, `pgbouncer` or `CONN_MAX_AGE` setting would help

---

## Authentication and Role Design

**Custom User Model:**
Django strongly recommends creating a custom user model at project start. `AbstractUser` was chosen over `AbstractBaseUser` — it keeps all default Django auth behaviour (username, password hashing, admin integration) and only adds the `role` field. Switching to a custom model mid-project requires resetting all migrations, which was done during development.

**Three roles:**

| Role | Can do |
|------|--------|
| Admin | Full access — all projects and KPIs |
| Project Owner | Create projects, manage only own projects and KPIs |
| Viewer | Read-only access to all projects and KPI summaries |

Role checks happen in views via `raise PermissionDenied` — server-side enforcement. UI also hides buttons based on role (template-level) but this is cosmetic only. The real guard is in the view.

**`request.user` available in all templates** via Django's `auth` context processor — no need to pass user manually to every `render()` call.

---

## Assumptions Around Authentication and Roles

- **Self-selected roles** — users pick their own role at registration. There is no admin approval step or invite system. This is a known security gap: anyone can register as Admin. Acceptable for an internal tool with trusted users, not acceptable for a public-facing product.
- **No email verification** — accounts are active immediately after registration. Fake or duplicate accounts are possible.
- **No password reset** — if a user forgets their password, an admin must reset it via Django admin (`/admin/`). A full password reset flow (email link) was not implemented.
- **No multi-tenancy** — all data is visible based on role, not organisation. A single deployment serves all users in one shared database. Adding tenancy would require a `Organisation` model and filtering every query by org.
- **No session timeout** — sessions persist until logout. For sensitive business data, a configurable session expiry should be added.

---

## Trade-offs Made During Implementation

| Decision | Trade-off |
|----------|-----------|
| Django monolith over API + SPA | Faster to build, harder to add a mobile app later |
| Manual role selection at registration | Simple UX, but anyone can claim Admin role |
| `kpi_summary` as a model property | Clean to use in templates, causes N+1 queries at scale |
| `WhiteNoise` for static files | No extra infrastructure needed, but not as performant as a CDN at high traffic |
| Hardcoded role thresholds (90/70%) | Simple and transparent, but not configurable per project |
| `DecimalField` for values | Precision over performance — slightly slower than `FloatField` |
| No pagination | Simpler code, breaks at large dataset sizes |
| Plain Bootstrap templates | Fast to build, no interactivity — full page reload on every action |

---

## Shortcuts Taken Due to Exercise Timeline

- **No email verification on registration** — would require an email backend (SendGrid, SES) and a token flow
- **No password reset flow** — skipped in favour of admin-managed resets
- **N+1 query on project list** — `kpi_summary` property works correctly but is not query-optimised; `annotate()` approach identified but not implemented
- **No pagination** — list views load all records; acceptable at small scale
- **No test suite** — no unit or integration tests written; models and views are manually tested only
- **No rate limiting on login** — brute force attacks on the login form are not prevented
- **`STATICFILES_DIRS` warning** — the `static/` directory referenced in settings does not exist; warning appears on every startup but does not affect functionality
- **Role-based access in templates is cosmetic** — buttons are hidden but a determined user who knows the URL can attempt to access edit/delete pages; server-side `PermissionDenied` is the real guard
