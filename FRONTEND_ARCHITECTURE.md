# Frontend Architecture — KPI Platform

Detailed breakdown of the React frontend: structure, routing, auth, state management, API communication, and per-component design.

---

## 1. Tech Stack

| Technology | Version | Role |
|------------|---------|------|
| React | 18 | UI library — component-based rendering |
| Vite | Latest | Build tool and dev server (replaces CRA) |
| React Router v6 | Latest | Client-side routing |
| axios | Latest | HTTP client for API calls |
| Bootstrap 5 | Latest (npm) | Responsive layout, UI components |
| Chart.js | Latest | KPI health doughnut charts |

Bootstrap is installed via npm (not CDN), imported in `main.jsx` — allows Vite to bundle only what's used.

---

## 2. Project Structure

```
frontend/
  src/
    api/
      axios.js          ← axios instance + JWT request interceptor
    components/
      Navbar.jsx        ← Persistent top navigation bar
    pages/
      Login.jsx         ← JWT login form
      Register.jsx      ← User registration form
      ProjectList.jsx   ← Paginated project cards grid
      ProjectDetail.jsx ← Single project + KPI management
      KpiTable.jsx      ← Cross-project KPI table with search/filter
    App.jsx             ← Router config + PrivateRoute guard
    main.jsx            ← React entry point, Bootstrap import
    index.css           ← Global style overrides
  .env.local            ← VITE_API_BASE_URL for local dev
  .env.production       ← VITE_API_BASE_URL for production (Railway URL)
  vite.config.js        ← Vite config
  package.json
```

---

## 3. Entry Point

### `main.jsx`

```jsx
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
)
```

- Mounts React app into the `<div id="root">` in `index.html`
- Imports `bootstrap/dist/css/bootstrap.min.css` and `bootstrap.bundle.min.js` — makes Bootstrap available globally across all components
- `StrictMode` double-invokes lifecycle methods in dev to surface side effects

---

## 4. Routing (`App.jsx`)

```
/               → redirect to /projects
/login          → Login (public)
/register       → Register (public)
/projects       → ProjectList (protected)
/projects/:id   → ProjectDetail (protected)
/kpis           → KpiTable (protected)
```

### PrivateRoute

```jsx
function PrivateRoute({ children }) {
  return localStorage.getItem('access') ? children : <Navigate to="/login" />;
}
```

Guards protected routes by checking for a JWT access token in `localStorage`. If absent, redirects to `/login`. This is a **client-side guard only** — the real protection is the API returning 401 for invalid/missing tokens.

### Layout

`<Navbar />` sits outside `<Routes>` — renders on every page including login/register. It conditionally shows the username/logout only when `localStorage('username')` exists, so it appears empty on public pages.

---

## 5. API Communication Layer (`api/axios.js`)

```js
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### How it works

1. `axios.create()` creates a dedicated instance with the API base URL — all relative paths (`/projects/`) resolve against it
2. `VITE_API_BASE_URL` is injected at build time by Vite from `.env.local` (dev) or `.env.production` (production build)
3. The **request interceptor** runs before every outgoing request — reads the JWT access token from `localStorage` and attaches it as a Bearer token header
4. Every component imports `api` from this file — no component constructs its own axios instance

### Environment switching

| Environment | `VITE_API_BASE_URL` value |
|-------------|--------------------------|
| Local dev | `http://localhost:8000/api` |
| Production | `https://kpiplatformapp-production.up.railway.app/api` |

Vite replaces `import.meta.env.VITE_API_BASE_URL` at bundle time — the built JS contains the literal URL string, not the env var reference.

### Paginated response handling

The backend API returns a paginated envelope on all list endpoints:
```json
{ "count": 42, "next": ".../?page=2", "previous": null, "results": [...] }
```

Components must access `.results` for data and `.count`/`.next` for pagination. Each component handles this differently — see Section 8.

---

## 6. Authentication

### Token storage

After login or register, four values are stored in `localStorage`:

| Key | Value | Source |
|-----|-------|--------|
| `access` | JWT access token (60 min TTL) | `/api/auth/login/` or `/api/auth/register/` response |
| `refresh` | JWT refresh token (7 day TTL) | Same response |
| `username` | Logged-in username | `/api/auth/me/` response |
| `role` | User role (admin / owner / viewer) | `/api/auth/me/` response |

### Login flow (`Login.jsx`)

```
User submits form
      │
      ▼
POST /api/auth/login/ { username, password }
      │
  Success → store access + refresh in localStorage
      │
      ▼
GET /api/auth/me/   ← needs Bearer token just stored
      │
  Success → store username + role in localStorage
      │
      ▼
navigate('/projects')
```

Two-step process: login returns tokens but not role. `/auth/me/` is called immediately after to get the role, which determines what buttons the UI shows.

### Register flow (`Register.jsx`)

```
User submits form { username, email, password, role }
      │
      ▼
POST /api/auth/register/
      │
  Success → response includes { access, refresh, username, role }
  (register returns everything in one call — no /auth/me/ needed)
      │
      ▼
Store all four values in localStorage
      │
      ▼
navigate('/projects')
```

Register returns role directly in the response (the backend `RegisterView` includes it). Login requires a second `/auth/me/` call because `TokenObtainPairView` (simplejwt built-in) only returns tokens.

### Logout (`Navbar.jsx`)

```js
function handleLogout() {
  localStorage.clear();
  navigate('/login');
}
```

Clears all localStorage keys. Tokens are not blacklisted server-side — they remain valid until their TTL expires. Acceptable tradeoff for this scope (no token revocation endpoint implemented).

### Known gaps

- **No auto-refresh:** Access token expires after 60 min. User must re-login manually. A refresh interceptor would call `POST /auth/refresh/` with the refresh token before the access token expires.
- **XSS risk:** localStorage is accessible by any JS on the page. `httpOnly` cookies would prevent this but require CSRF handling.

---

## 7. State Management Approach

No global state library (no Redux, no Zustand, no Context API). Each page component manages its own local state with `useState`. Data is fetched fresh on mount via `useEffect`.

This is intentional: the app has no shared mutable state between pages. Each page is independent — navigating to `/projects` always fetches from the API.

**Consequence:** navigating back to `ProjectList` after creating a KPI in `ProjectDetail` will re-fetch and show updated data automatically.

---

## 8. Components

### 8.1 `Navbar.jsx`

**Reads:** `localStorage('username')`, `localStorage('role')`  
**No API calls.**

Renders the top nav bar on every page. Shows:
- "KPI Platform" brand link → `/projects`
- "All KPIs" link → `/kpis`
- Username + role badge (only when logged in)
- Logout button (only when logged in)

Role display is read directly from `localStorage` on every render — no React state. If `username` is null (not logged in), the user section is hidden.

---

### 8.2 `Login.jsx`

**State:** `username`, `password`, `error`  
**API calls:** `POST /auth/login/`, `GET /auth/me/`

Controlled form — each input is a `useState` value. On submit:
1. Calls `/auth/login/` with credentials
2. On success, stores `access` + `refresh` in localStorage
3. Immediately calls `/auth/me/` to get `username` + `role`
4. Navigates to `/projects`
5. On failure, sets `error` state → shows Bootstrap alert

---

### 8.3 `Register.jsx`

**State:** `form` object `{ username, email, password, role }`, `error`  
**API calls:** `POST /auth/register/`

Single form object state — `handleChange` uses `e.target.name` to update the correct key without needing individual state per field:
```js
setForm({ ...form, [e.target.name]: e.target.value })
```

Role dropdown lets user self-select admin/owner/viewer. Registration response includes tokens + role — redirects to `/projects` immediately.

---

### 8.4 `ProjectList.jsx`

**State:** `projects[]`, `totalCount`, `page`, `showModal`, `form`  
**API calls:** `GET /api/projects/?page=N`, `POST /api/projects/`

#### Pagination strategy: true server-side

```
page state changes
      │
      ▼
useEffect([page]) fires
      │
      ▼
GET /api/projects/?page={page}
      │
      ▼
setProjects(res.data.results)   ← 10 projects
setTotalCount(res.data.count)   ← total across all pages
      │
      ▼
totalPages = Math.ceil(totalCount / 10)
      │
      ▼
Render 10 project cards + pagination controls
```

Page number drives the API call — server returns only the requested page. Changing page triggers `useEffect` re-run.

#### Project card content

Each card shows:
- Project name, description, owner username
- KPI status counts: `✓ on_track`, `⚠ at_risk`, `✗ off_track` (from serializer)
- Overall status badge (Off Track if any off_track > 0, At Risk if any at_risk > 0, On Track otherwise)
- Clicking card navigates to `/projects/:id`

#### Create project modal

Inline modal (no library) — `showModal` boolean controls visibility via Bootstrap class `show d-block`. Form posts to `/api/projects/` then reloads current page.

#### Role check

```jsx
{role !== 'viewer' && <button>+ New Project</button>}
```

Viewers don't see the create button. Cosmetic only — API enforces the real restriction.

---

### 8.5 `ProjectDetail.jsx`

**State:** `project`, `kpis[]`, `showKpiModal`, `editingKpi`, `kpiForm`  
**API calls:** `GET /api/projects/:id/`, `GET /api/projects/:id/kpis/` (all pages), `POST`, `PUT`, `DELETE` on KPIs, `DELETE` on project

#### KPI loading: fetch all pages

```js
async function loadKpis() {
  let results = [];
  let url = `/projects/${id}/kpis/`;
  while (url) {
    const res = await api.get(url);
    results = [...results, ...res.data.results];
    url = res.data.next;   // null when last page reached
  }
  setKpis(results);
}
```

Chases `next` links until exhausted. Handles projects with any number of KPIs correctly. No pagination UI on this page — all KPIs shown as cards.

#### KPI cards

Each card shows:
- KPI name and description
- `actual / target unit` + `progress_percent`
- Bootstrap progress bar (colour: green/yellow/red by status)
- Status badge

#### Edit KPI modal

`openEditKpi(kpi)` pre-populates `kpiForm` with existing values and sets `editingKpi`. Same modal component used for both create and edit — `saveKpi()` branches on `editingKpi`:
```js
editingKpi ? api.put(...) : api.post(...)
```

#### Ownership check

```js
const canEdit = role === 'admin' || project?.owner_username === username;
```

Both admin and the project's own owner see edit/delete buttons. Viewer and other owners do not.

#### Delete project

`window.confirm()` dialog before delete. On confirm, calls `DELETE /api/projects/:id/` and navigates back to `/projects`.

---

### 8.6 `KpiTable.jsx`

**State:** `kpis[]` (all KPIs, cross-project), `page`, `search`, `statusFilter`  
**API calls:** all project pages + all KPI pages per project (N+1 pattern)

#### Data loading: fetch everything

```js
async function fetchAllPages(url) {
  let results = [];
  let next = url;
  while (next) {
    const res = await api.get(next);
    results = [...results, ...res.data.results];
    next = res.data.next;
  }
  return results;
}

async function loadAll() {
  const allProjects = await fetchAllPages('/projects/');
  const allKpis = [];
  for (const project of allProjects) {
    const kpis = await fetchAllPages(`/projects/${project.id}/kpis/`);
    kpis.forEach(k => allKpis.push({
      ...k,
      project_name: project.name,
      project_id: project.id
    }));
  }
  setKpis(allKpis);
}
```

With 20 projects (seed data): 2 project-page calls + 20 KPI calls = 22 API calls on load. Sequential — each project's KPIs fetched in order.

`project_name` and `project_id` are attached to each KPI manually because the KPI serializer only returns `project` (the ID). The project name comes from the project object fetched earlier.

#### Client-side filtering

```js
const filtered = kpis.filter(k => {
  const matchSearch = k.name.toLowerCase().includes(search.toLowerCase()) ||
    k.project_name.toLowerCase().includes(search.toLowerCase());
  const matchStatus = statusFilter ? k.status === statusFilter : true;
  return matchSearch && matchStatus;
});
```

Search matches KPI name OR project name. Status filter is exact match. Both run on the full in-memory dataset.

#### Client-side pagination

```js
const totalPages = Math.ceil(filtered.length / perPage);  // perPage = 10
const paginated = filtered.slice((page - 1) * perPage, page * perPage);
```

Pagination resets to page 1 when search or filter changes (`setPage(1)` in onChange handlers).

---

## 9. Role-Based UI Summary

| Component | What changes by role |
|-----------|---------------------|
| `ProjectList` | "New Project" button hidden for viewers |
| `ProjectDetail` | Edit/Delete KPI buttons + Delete Project button hidden for viewers and non-owners |
| `KpiTable` | Read-only — no role-based changes |
| `Navbar` | Displays role label next to username |

All role checks read `localStorage.getItem('role')`. This is cosmetic — no component prevents an API call based on role. The API returns 403 for unauthorised actions regardless of what the UI shows.

---

## 10. Data Flow Diagram

### Page load (ProjectList)

```
Browser navigates to /projects
         │
         ▼
PrivateRoute checks localStorage('access')
         │
  Token exists → render ProjectList
         │
         ▼
useEffect([page]) → loadProjects()
         │
         ▼
api.get('/projects/?page=1')
  → interceptor adds Authorization: Bearer <token>
  → request to Railway API
         │
         ▼
API returns { count: 20, next: "...?page=2", results: [...10 projects] }
         │
         ▼
setProjects(results) → setTotalCount(20)
         │
         ▼
React re-renders → 10 project cards + pagination (2 pages)
```

### Mutation (create KPI in ProjectDetail)

```
User fills modal → clicks Save
         │
         ▼
saveKpi() → api.post('/projects/3/kpis/', kpiForm)
  → interceptor adds Bearer token
  → 201 Created + new KPI JSON
         │
         ▼
setShowKpiModal(false)
         │
         ▼
loadKpis() re-fetches all KPI pages for project 3
         │
         ▼
setKpis(updatedList) → React re-renders cards
```

---

## 11. Known Limitations

| Issue | Impact | Fix |
|-------|--------|-----|
| No JWT auto-refresh | User logged out after 60 min access token expiry | axios response interceptor: on 401, call `POST /auth/refresh/`, retry original request |
| `localStorage` token storage | XSS attack can read tokens | `httpOnly` cookies + CSRF token handling |
| KpiTable loads all data on mount | Slow with large datasets (20+ projects × many KPIs) | Dedicated `/api/kpis/?search=&status=` endpoint with server-side filtering |
| No loading states | UI shows nothing while API calls are in flight | `isLoading` state → show spinner |
| No error handling on API failures | Failed requests silently show empty data | try/catch with error state → user-facing message |
| Self-selected roles | Anyone can register as Admin | Backend approval flow or invite-only registration |
| `navigate('/projects')` called twice in Login | Harmless but a bug | Remove the duplicate line |
