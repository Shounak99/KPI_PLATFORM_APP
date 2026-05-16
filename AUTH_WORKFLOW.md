# Authorization Workflow — KPI Platform

Covers authentication (who are you?) and authorization (what can you do?) end-to-end: token lifecycle, role definitions, permission enforcement per endpoint, and the frontend guard layer.

---

## 1. Actors

| Role | How assigned | What they represent |
|------|-------------|---------------------|
| `admin` | Self-selected at registration | Platform administrator — full access |
| `owner` | Self-selected at registration | Project creator — manages own projects |
| `viewer` | Default if none selected | Read-only consumer of data |

Roles are stored in `accounts_customuser.role`. No admin approval step — users self-declare their role.

---

## 2. Authentication — How Identity is Established

### 2.1 Token Types

| Token | Lifetime | Purpose |
|-------|----------|---------|
| Access token (JWT) | 60 minutes | Proves identity on every API request |
| Refresh token (JWT) | 7 days | Used to get a new access token after expiry |

Both are signed with `SECRET_KEY`. Django never stores them — they are stateless. Validity is proven by signature verification on each request.

### 2.2 Register Flow

```
POST /api/auth/register/
Body: { username, password, email, role }

        │
        ▼
RegisterView (permission_classes = [AllowAny])
        │
        ├── username or password missing? → 400 Bad Request
        ├── username already exists?      → 400 Bad Request
        │
        ▼
CustomUser.objects.create_user(...)
  → password hashed with PBKDF2 before storage
        │
        ▼
RefreshToken.for_user(user)
  → generates access + refresh JWT pair
        │
        ▼
201 Created
{ access, refresh, username, role }
        │
        ▼
React stores in localStorage:
  access, refresh, username, role
        │
        ▼
Redirect → /projects
```

Register returns the role in one call — no second request needed.

---

### 2.3 Login Flow

```
POST /api/auth/login/
Body: { username, password }

        │
        ▼
TokenObtainPairView (simplejwt built-in)
  → validates credentials against DB
  → password check via Django's PBKDF2 verifier
        │
  Valid?
  /          \
Yes            No
 │              │
 ▼              ▼
200 OK        401 Unauthorized
{ access,     { detail: "No active account found
  refresh }     with the given credentials" }
 │
 ▼
React stores access + refresh in localStorage
        │
        ▼
GET /api/auth/me/
  Authorization: Bearer <access>
        │
        ▼
Returns { username, role, email }
        │
        ▼
React stores username + role in localStorage
        │
        ▼
Redirect → /projects
```

Login requires two calls because `TokenObtainPairView` (simplejwt built-in) only returns tokens — it does not return role. The `/auth/me/` call fetches user info using the newly obtained token.

---

### 2.4 How Every Authenticated Request Works

```
React component calls api.get('/projects/')
        │
        ▼
axios request interceptor fires:
  token = localStorage.getItem('access')
  config.headers.Authorization = `Bearer ${token}`
        │
        ▼
Request arrives at Django API
        │
        ▼
JWTAuthentication.authenticate()
  → extracts Bearer token from Authorization header
  → decodes JWT signature using SECRET_KEY
  → checks token expiry (exp claim)
  → looks up user by ID embedded in token
  → sets request.user = CustomUser instance
        │
  Token valid?
  /           \
Yes             No
 │               │
 ▼               ▼
View executes   401 Unauthorized
                { detail: "Given token not valid
                  for any token type" }
```

---

### 2.5 Token Expiry and Refresh

```
Access token expires after 60 min

Currently: user must log in again manually (no auto-refresh)

Correct fix (not implemented):
  axios response interceptor catches 401
        │
        ▼
  POST /api/auth/refresh/
  Body: { refresh: localStorage.getItem('refresh') }
        │
        ▼
  Returns { access: <new_token> }
        │
        ▼
  Update localStorage('access')
        │
        ▼
  Retry original request with new token

Refresh token expires after 7 days → full re-login required
```

---

### 2.6 Logout

```
Navbar → handleLogout()
        │
        ▼
localStorage.clear()
  removes: access, refresh, username, role
        │
        ▼
navigate('/login')
```

Tokens are **not invalidated server-side** — they remain cryptographically valid until their TTL expires. No token blacklist is implemented. Acceptable tradeoff: access token only lives 60 min.

---

## 3. Authorization — What Each Role Can Do

### 3.1 Role Capability Matrix

| Action | Admin | Owner | Viewer |
|--------|-------|-------|--------|
| View all projects | ✅ | ✅ (own only in queryset) | ✅ |
| Create project | ✅ | ✅ | ❌ 403 |
| Edit any project | ✅ | ❌ 403 (others' projects) | ❌ 403 |
| Edit own project | ✅ | ✅ | ❌ 403 |
| Delete any project | ✅ | ❌ 403 | ❌ 403 |
| Delete own project | ✅ | ✅ | ❌ 403 |
| View all KPIs | ✅ | ✅ (own projects only) | ✅ |
| Create KPI | ✅ | ✅ | ❌ 403 |
| Edit/Delete KPI | ✅ | ✅ | ❌ 403 |
| Access Django admin | ✅ (if is_staff=True) | ❌ | ❌ |

---

### 3.2 How the API Enforces Permissions

All endpoints require authentication (`IsAuthenticated` global default in `REST_FRAMEWORK` settings). Role checks happen inside view methods, not as DRF permission classes — they raise `PermissionDenied` (HTTP 403) directly.

#### Projects — `ProjectViewSet`

**GET /api/projects/** (list)
```python
def get_queryset(self):
    if user.is_admin() or user.is_viewer():
        return Project.objects.all()       # see everything
    return Project.objects.filter(owner=user)  # owner: own projects only
```
Viewers and admins see all projects. Owners only see theirs.

**POST /api/projects/** (create)
```python
def perform_create(self, serializer):
    if request.user.is_viewer():
        raise PermissionDenied(...)        # 403
    serializer.save(owner=request.user)   # project owner = logged-in user
```

**PUT/PATCH /api/projects/\<id\>/** (update)
```python
def perform_update(self, serializer):
    if not user.is_admin() and project.owner != user:
        raise PermissionDenied(...)        # 403 if not admin and not owner
    serializer.save()
```

**DELETE /api/projects/\<id\>/** (destroy)
```python
def perform_destroy(self, instance):
    if not user.is_admin() and instance.owner != user:
        raise PermissionDenied(...)        # 403
    instance.delete()
```

---

#### KPIs (nested) — `KPIViewSet`

**GET /api/projects/\<pk\>/kpis/** (list)
```python
def get_queryset(self):
    return KPI.objects.filter(project_id=self.kwargs['project_pk'])
```
No extra role filtering — all authenticated users can read KPIs for any project they can access. Access to the parent project is the implicit gate.

**POST /api/projects/\<pk\>/kpis/** (create)
```python
def perform_create(self, serializer):
    if request.user.is_viewer():
        raise PermissionDenied(...)        # 403
    project = get_object_or_404(Project, pk=project_pk)
    serializer.save(project=project)
```

Note: KPI update/delete has no explicit ownership check in `KPIViewSet` — the parent project ownership is not re-verified. Known gap: an owner could potentially edit KPIs on another owner's project if they know the URL.

---

#### All KPIs — `AllKPIsView`

**GET /api/kpis/** (list, with search and status filter)
```python
def get_queryset(self):
    if user.is_project_owner():
        queryset = KPI.objects.filter(project__owner=user)  # own projects only
    else:
        queryset = KPI.objects.all()                         # admin + viewer: all
```

---

### 3.3 Permission Decision Tree (per API request)

```
Request arrives
      │
      ▼
Is Authorization header present and token valid?
      │
  No  │  Yes
  │   │
  ▼   ▼
 401  request.user = CustomUser (with role)
      │
      ▼
Is endpoint public? (register, login, refresh)
      │
  Yes │  No
  │   │
  ▼   ▼
Skip  IsAuthenticated check passes (token already valid)
      │
      ▼
ViewSet action executes role check:
      │
  ┌───┴──────────────────────────────────────┐
  │                                          │
Viewer?                               Admin or Owner?
  │                                          │
Write action?                         Ownership check needed?
  │                                          │
  ▼                                    /          \
403 PermissionDenied            Own resource?   Admin?
                                    │               │
                                   Allow           Allow
                                    │
                                Other's resource?
                                    │
                                   403
```

---

## 4. Frontend Auth Layer

The frontend has two layers — both are **cosmetic only**. The API is the real enforcement.

### 4.1 Route Guard (PrivateRoute)

```jsx
function PrivateRoute({ children }) {
  return localStorage.getItem('access') ? children : <Navigate to="/login" />;
}
```

Blocks unauthenticated users from seeing protected pages. Does not validate the token — only checks presence. A stored expired token would pass this check but fail on the first API call (401).

### 4.2 UI Role Checks

```jsx
// ProjectList — hide create button
{role !== 'viewer' && <button>+ New Project</button>}

// ProjectDetail — hide edit/delete buttons
const canEdit = role === 'admin' || project?.owner_username === username;
{canEdit && <button>Edit</button>}
```

`role` is read from `localStorage` — set after login/register. These checks hide UI elements but cannot prevent API calls. A viewer who manually calls `POST /api/projects/` via curl or Postman gets 403 from the server regardless.

---

## 5. Token Security Tradeoffs

| Risk | Current approach | Safer alternative |
|------|-----------------|-------------------|
| XSS can read tokens | localStorage | `httpOnly` cookies (JS cannot access) |
| No token revocation | Tokens valid until TTL | Token blacklist in Redis/DB |
| No refresh interceptor | User re-logs after 60 min | axios 401 interceptor with auto-refresh |
| Self-selected roles | Anyone claims Admin | Invite system or admin approval flow |
| No rate limiting on login | Brute force possible | Django `django-ratelimit` or API gateway |

All known — documented as accepted tradeoffs for this project scope. See `DECISIONS.md`.
