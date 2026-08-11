# Guardrail

> **Security guardrails for growing businesses.**

Guardrail is a cybersecurity platform designed for small and growing businesses that don't have dedicated cybersecurity teams. The long-term product will identify, prioritize, explain, and help remediate security risks across code, cloud infrastructure, identities, and connected services.

---

## Current Phase

**Phase 1 — Foundation**

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
- **Testing:** pytest & FastAPI TestClient

---

## Project Structure

```text
guardrail/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── ProtectedRoute.tsx
│   │   ├── context/
│   │   │   └── AuthContext.tsx
│   │   ├── layouts/
│   │   │   └── DashboardLayout.tsx
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   └── DashboardPage.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── auth.ts
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
│   │   │   │   └── auth.py
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   └── user.py
│   │   ├── schemas/
│   │   │   └── user.py
│   │   ├── services/
│   │   │   └── auth_service.py
│   │   └── main.py
│   │
│   ├── migrations/
│   │   ├── versions/
│   │   │   └── 2026_08_11_0001_create_users_table.py
│   │   └── env.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_health.py
│   │   ├── test_auth.py
│   │   └── test_security.py
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

## Future Roadmap

- **Phase 1 → Foundation** *(Completed)*
- **Phase 2 → Repository Management**
- **Phase 3 → Secret Scanner**
- **Phase 4 → Dependency Scanner**
- **Phase 5 → Risk Engine**
- **Phase 6 → Security Dashboard**
- **Phase 7 → AI Copilot**
- **Phase 8 → GitHub Integration**
- **Phase 9 → Cloud Security**
- **Phase 10 → Security Graph**
