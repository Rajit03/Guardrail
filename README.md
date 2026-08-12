# Guardrail

> **Security guardrails for growing businesses.**

Guardrail is a cybersecurity platform designed for small and growing businesses that don't have dedicated cybersecurity teams. The long-term product will identify, prioritize, explain, and help remediate security risks across code, cloud infrastructure, identities, and connected services.

---

## Current Phase

**Phase 2 — Repository Management**

---

## Completed

**Phase 1 — Foundation:**
- Authentication (registration, login, JWT)
- PostgreSQL with SQLAlchemy & Alembic
- Docker Compose orchestration
- Protected dashboard

**Phase 2 — Repository Management:**
- Repository management UI (`/repositories`)
- Repository CRUD API (`/api/repositories`)
- Per-user repository ownership & isolation
- GitHub URL validation
- Repository count on dashboard

---

## Features

- **User Registration (`POST /api/auth/register`):** Email validation, password strength validation, Argon2id password hashing, duplicate email rejection.
- **Secure Login (`POST /api/auth/login`):** Credentials authentication, expiring JWT bearer token generation.
- **Current User Identity (`GET /api/auth/me`):** Protected bearer token validation returning user profile (strictly omitting passwords and hashes).
- **Service Health Check (`GET /api/health`):** Public health check returning API status.
- **PostgreSQL Database:** Integrated via SQLAlchemy 2.0 ORM with declarative UUID `User` model.
- **Alembic Database Migrations:** Versioned schema migrations (`alembic upgrade head`).
- **Protected Dashboard UI:** React 18 + TypeScript + Vite + Tailwind CSS dashboard with sidebar navigation, security score metrics, and empty state banner.
- **Docker Compose Orchestration:** Multi-container setup for `postgres` (with persistent volume), `backend` (FastAPI), and `frontend` (React/Vite).
- **API Documentation:** Interactive OpenAPI Swagger UI accessible at `/docs`.
- **Automated Test Suite:** Comprehensive pytest test suite covering registration, login, JWT validation, health check, password security, and SQL parameterization safety.
- **Repository Management (`/api/repositories`):** Authenticated CRUD endpoints for registering GitHub repositories, with strict per-user ownership (other users' repositories return `404`), GitHub URL validation, and an immutable repository URL.
- **Repository UI (`/repositories`):** Repository cards with add/edit/delete modals, delete confirmation dialog, repository details page with a placeholder scan action (scanning arrives in Phase 3), and real repository count on the dashboard.
- **Frontend Test Suite:** Vitest + React Testing Library tests covering the repository list, add/edit/delete flows, validation errors, empty state, and auth redirects.

---

## Technology Stack

### Frontend
- **Framework:** React 18 + TypeScript + Vite
- **Styling:** Tailwind CSS
- **Routing:** React Router v6
- **HTTP Client:** Axios (with request/response interceptors)
- **Icons:** Lucide React

### Backend
- **Framework:** Python 3.12+ / FastAPI
- **ORM:** SQLAlchemy 2.0
- **Database:** PostgreSQL 16
- **Migrations:** Alembic
- **Auth & Security:** JWT tokens (PyJWT / python-jose), Argon2id password hashing (`argon2-cffi`)
- **Validation:** Pydantic v2

### Infrastructure & Testing
- **Orchestration:** Docker & Docker Compose
- **Testing:** pytest & FastAPI TestClient (backend), Vitest & React Testing Library (frontend)

---

## Project Structure

```text
guardrail/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ProtectedRoute.tsx
│   │   │   ├── RepositoryFormModal.tsx
│   │   │   ├── DeleteRepositoryModal.tsx
│   │   │   └── Toast.tsx
│   │   ├── context/
│   │   │   └── AuthContext.tsx
│   │   ├── layouts/
│   │   │   └── DashboardLayout.tsx
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── RepositoriesPage.tsx
│   │   │   └── RepositoryDetailPage.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── auth.ts
│   │   │   └── repositories.ts
│   │   ├── tests/
│   │   │   ├── setup.ts
│   │   │   └── repositories.test.tsx
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── health.py
│   │   │   │   ├── auth.py
│   │   │   │   └── repositories.py
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   └── repository.py
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   └── repository.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   └── repository_service.py
│   │   └── main.py
│   │
│   ├── migrations/
│   │   ├── versions/
│   │   │   ├── 2026_08_11_0001_create_users_table.py
│   │   │   └── 2026_08_12_0002_create_repositories_table.py
│   │   └── env.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_health.py
│   │   ├── test_auth.py
│   │   ├── test_security.py
│   │   └── test_repositories.py
│   ├── requirements.txt
│   ├── alembic.ini
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## API Reference

| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | No | Service health check |
| `POST` | `/api/auth/register` | No | Register a new user account |
| `POST` | `/api/auth/login` | No | Authenticate user & return JWT token |
| `GET` | `/api/auth/me` | Yes (Bearer) | Get profile of currently authenticated user |
| `POST` | `/api/repositories` | Yes (Bearer) | Register a new repository |
| `GET` | `/api/repositories` | Yes (Bearer) | List repositories owned by current user |
| `GET` | `/api/repositories/{id}` | Yes (Bearer) | Get repository details |
| `PATCH` | `/api/repositories/{id}` | Yes (Bearer) | Update repository (name, branch, description, active status) |
| `DELETE` | `/api/repositories/{id}` | Yes (Bearer) | Delete repository |
| `GET` | `/docs` | No | Interactive Swagger API Documentation |

---

## Database Model (`User`)

| Field | Type | Attributes |
| :--- | :--- | :--- |
| `id` | UUID | Primary Key, Indexed |
| `name` | String(255) | Not Null |
| `email` | String(255) | Unique, Indexed, Not Null |
| `password_hash` | String(255) | Argon2id Hash, Not Null |
| `is_active` | Boolean | Default: True, Not Null |
| `created_at` | DateTime | UTC Timestamp, Not Null |
| `updated_at` | DateTime | UTC Timestamp, Not Null |

---

## Database Model (`Repository`)

| Field | Type | Attributes |
| :--- | :--- | :--- |
| `id` | UUID | Primary Key, Indexed |
| `user_id` | UUID | Foreign Key → `users.id` (ON DELETE CASCADE), Indexed, Not Null |
| `name` | String(100) | Not Null |
| `url` | String(500) | GitHub URL, immutable after creation, Not Null |
| `provider` | String(50) | Default: `github`, Not Null |
| `default_branch` | String(255) | Default: `main`, Not Null |
| `description` | Text | Optional |
| `is_active` | Boolean | Default: True, Not Null |
| `created_at` | DateTime | UTC Timestamp, Not Null |
| `updated_at` | DateTime | UTC Timestamp, Not Null |
| `last_scan_at` | DateTime | Nullable (used by Phase 3+ scanning) |

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ and Python 3.12+ (for local development outside Docker)

### Running with Docker Compose (Recommended)

1. Clone the repository.
2. Copy environment template:
   ```bash
   cp .env.example .env
   ```
3. Start containers with build:
   ```bash
   docker compose up --build
   ```
4. Access the application:
   - **Guardrail Web App:** [http://localhost:5173](http://localhost:5173)
   - **FastAPI Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Backend Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

To reset containers and persistent volume:
```bash
docker compose down -v
docker compose up --build
```

---

## Running Local Backend Tests

1. Navigate to `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies and run tests:
   ```bash
   pip install -r requirements.txt
   pytest -v
   ```

---

## Running Frontend Tests

1. Navigate to `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies and run tests:
   ```bash
   npm install
   npm test
   ```

---

## Future Roadmap

- **Phase 1 → Foundation** *(Completed)*
- **Phase 2 → Repository Management** *(Completed)*
- **Phase 3 → Security Scanning**
- **Phase 4 → Risk Engine**
- **Phase 5 → Security Dashboard**
- **Phase 6 → AI Copilot**
- **Phase 7 → GitHub Integration**
- **Phase 8 → Cloud Security**
- **Phase 9 → Security Graph**
- **Phase 10 → SaaS MVP**
