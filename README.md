# Guardrail

> **Security guardrails for growing businesses.**

Guardrail is a cybersecurity platform designed for small and growing businesses that don't have dedicated cybersecurity teams. The long-term product will identify, prioritize, explain, and help remediate security risks across code, cloud infrastructure, identities, and connected services.

---

## Current Phase

**Phase 1 — Foundation**

---

## Current Features

- User registration (`POST /api/auth/register`)
- Secure login & token generation (`POST /api/auth/login`)
- JWT bearer authentication (`GET /api/auth/me`)
- PostgreSQL database integration via SQLAlchemy 2.x
- Alembic database migration system
- Protected dashboard UI (React + Vite + TypeScript + Tailwind CSS)
- Docker Compose setup (`postgres`, `backend`, `frontend`)
- Interactive API documentation (`/docs`)
- Comprehensive automated pytest suite

---

## Technical Stack

### Frontend
- **Framework:** React 18 + TypeScript + Vite
- **Styling:** Tailwind CSS
- **Routing:** React Router v6
- **HTTP Client:** Axios

### Backend
- **Framework:** Python 3.12+ / FastAPI
- **ORM:** SQLAlchemy 2.x
- **Database:** PostgreSQL
- **Migrations:** Alembic
- **Auth & Security:** JWT tokens (PyJWT / python-jose), Password hashing (Argon2 / bcrypt)
- **Validation:** Pydantic v2

### Infrastructure & Testing
- **Orchestration:** Docker & Docker Compose
- **Testing:** pytest & FastAPI TestClient

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ and Python 3.12+ (for local development outside Docker)

### Running with Docker Compose

1. Clone the repository.
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Build and start the containers:
   ```bash
   docker compose up --build
   ```
4. Access the services:
   - **Frontend App:** [http://localhost:5173](http://localhost:5173)
   - **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Backend Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## Running Local Backend Tests

```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
pytest -v
```

---

## Future Roadmap

- **Phase 1 → Foundation** *(Current)*
- **Phase 2 → Repository Management**
- **Phase 3 → Secret Scanner**
- **Phase 4 → Dependency Scanner**
- **Phase 5 → Risk Engine**
- **Phase 6 → Security Dashboard**
- **Phase 7 → AI Copilot**
- **Phase 8 → GitHub Integration**
- **Phase 9 → Cloud Security**
- **Phase 10 → Security Graph**
