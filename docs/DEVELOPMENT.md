# Development Guide — Studentska Platforma

## 🚀 Quick Start

### Prerequisites
- Docker Desktop (macOS/Windows) or Docker + Docker Compose (Linux)
- Git

### 1. Clone Repository
```bash
git clone <repository>
cd studentska-platforma
```

### 2. Setup Environment
```bash
cp .env.example .env
```

### 3. Start Services
```bash
docker-compose up -d
```

Wait for all services to be healthy (~30s):
```bash
docker ps
# All containers should show "healthy" or "up"
```

### 4. Verify Setup
```bash
# Check FastAPI health
curl http://localhost:8000/health

# Check Keycloak
open http://localhost:8080/admin/master/console/
# Login: admin / admin

# Check Next.js
open http://localhost:3000
```

---

## 📂 Project Structure

```
backend/
  ├── app/
  │   ├── main.py              # FastAPI app factory
  │   ├── config.py            # Settings (pydantic)
  │   ├── models/              # SQLAlchemy ORM models
  │   ├── schemas/             # Pydantic request/response schemas
  │   ├── services/            # Business logic layer
  │   ├── tasks/               # Celery background jobs
  │   ├── api/v1/              # API endpoints v1
  │   │   ├── auth.py          # Authentication endpoints
  │   │   ├── students.py      # Student portal endpoints
  │   │   ├── professors.py    # Professor portal endpoints
  │   │   ├── appointments.py  # Appointment endpoints
  │   │   ├── admin.py         # Admin panel endpoints
  │   │   ├── search.py        # Search endpoints
  │   │   └── notifications.py # Notification endpoints
  │   ├── db/
  │   │   ├── database.py      # SQLAlchemy setup
  │   │   ├── base.py          # Declarative base
  │   │   └── init_db.py       # DB initialization
  │   └── utils/               # Utility functions
  ├── migrations/              # Alembic database migrations
  ├── tests/                   # Unit and integration tests
  └── requirements.txt

frontend/
  ├── src/
  │   ├── app/                 # Next.js App Router
  │   │   ├── layout.tsx       # Root layout
  │   │   ├── page.tsx         # Home page
  │   │   ├── (auth)/          # Auth group
  │   │   └── (protected)/     # Protected routes
  │   ├── components/          # React components
  │   ├── hooks/               # Custom React hooks
  │   ├── services/            # API client services
  │   ├── lib/                 # Utility functions
  │   └── styles/              # CSS/Tailwind
  ├── public/                  # Static assets
  └── package.json
```

---

## 🐳 Docker Compose Services

| Service | Port | Health Check |
|---------|------|--------------|
| PostgreSQL | 5432 | `psql -h localhost -U postgres` |
| Redis | 6379 | `redis-cli ping` |
| Keycloak | 8080 | `curl http://localhost:8080/health` |
| FastAPI | 8000 | `curl http://localhost:8000/health` |
| Next.js | 3000 | `curl http://localhost:3000` |
| MinIO | 9000/9001 | `curl http://localhost:9000/minio/health/live` |
| Celery | — | `docker logs studentska_celery` |

### Useful Docker Commands

```bash
# View running containers
docker ps

# View container logs
docker logs studentska_fastapi
docker logs studentska_nextjs

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Rebuild services after code changes
docker-compose build --no-cache
docker-compose up -d

# Access PostgreSQL CLI
docker exec -it studentska_postgres psql -U postgres -d studentska_platforma

# Access Redis CLI
docker exec -it studentska_redis redis-cli
```

---

## 💻 Backend Development

### Environment Variables
Copy `.env.example` to `.env` and adjust as needed.

**Key variables:**
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `KEYCLOAK_*` — Keycloak configuration
- `MINIO_*` — MinIO object storage configuration
- `SECRET_KEY` — App secret key
- `ENVIRONMENT` — development/production

### Running Backend Locally (without Docker)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost/studentska_platforma"
export REDIS_URL="redis://localhost:6379/0"
# ... set other variables

# Run Alembic migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
Once FastAPI is running:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

### Phase 2 API (Current)

Real-time chat i upload fajlova su sada dostupni:

- `GET /v1/chat/appointments/{appointment_id}/messages`
- `POST /v1/chat/appointments/{appointment_id}/messages`
- `WS /v1/chat/ws/appointments/{appointment_id}?token=<jwt>`
- `POST /v1/files/appointments/{appointment_id}/upload` (multipart/form-data, field `file`)
- `GET /v1/files/appointments/{appointment_id}`
- `GET /v1/files/appointments/{appointment_id}/{file_id}/download-url`

Napomena: pristup je dozvoljen samo učesnicima konsultacije (student/profesor) i admin-u.

#### WebSocket primer

```javascript
const ws = new WebSocket(
  `ws://localhost:8000/v1/chat/ws/appointments/${appointmentId}?token=${jwt}`
);

ws.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  console.log(payload.event, payload.data);
};

ws.send(JSON.stringify({ message: "Pozdrav profesore" }));
```

#### Upload primer

```bash
curl -X POST "http://localhost:8000/v1/files/appointments/<appointment_id>/upload" \
  -H "Authorization: Bearer <jwt>" \
  -F "file=@./primer.pdf"
```

#### Download URL primer

```bash
curl -X GET "http://localhost:8000/v1/files/appointments/<appointment_id>/<file_id>/download-url" \
  -H "Authorization: Bearer <jwt>"
```

Odgovor sadrzi privremeni `download_url` koji vazi 15 minuta.

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback to previous
alembic downgrade -1

# View migration history
alembic history
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_appointments.py

# Run specific test
pytest tests/test_appointments.py::test_create_appointment
```

---

## 🎨 Frontend Development

### Environment Variables
Frontend environment variables must start with `NEXT_PUBLIC_` to be accessible in the browser.

**Key variables:**
- `NEXT_PUBLIC_API_URL` — Backend API URL
- `NEXT_PUBLIC_KEYCLOAK_URL` — Keycloak server URL
- `NEXT_PUBLIC_KEYCLOAK_REALM` — Keycloak realm name
- `NEXT_PUBLIC_KEYCLOAK_CLIENT_ID` — Frontend client ID

### Running Frontend Locally (without Docker)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

Frontend will be available at http://localhost:3000

### Development Tools

```bash
# Format code with Prettier
npm run prettier

# Lint with ESLint
npm run lint

# Type checking
npm run type-check

# Build and start
npm run build && npm start
```

---

## 🔑 Keycloak SSO Setup

### Manual Setup (if auto-import fails)

1. Access Keycloak: http://localhost:8080/admin/master/console/
2. Login with `admin` / `admin`
3. Select "Realm" in top-left
4. Click "Create Realm" → Upload JSON from `infra/keycloak/imports/realm-config.json`
5. Or manually create:
   - Realm name: `fakultet`
   - Clients: `fakultet-backend`, `fakultet-frontend`
   - Roles: `student`, `asistent`, `profesor`, `admin`

### Test SSO Login

```bash
# Get access token
curl -X POST http://localhost:8080/realms/fakultet/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=fakultet-backend" \
  -d "client_secret=change-me-in-production" \
  -d "grant_type=client_credentials"
```

---

## 📊 Database

### PostgreSQL

Access PostgreSQL:
```bash
docker exec -it studentska_postgres psql -U postgres -d studentska_platforma
```

Common queries:
```sql
-- List all tables
\dt

-- View users
SELECT * FROM users;

-- View appointments
SELECT * FROM appointments;

-- Count appointments by status
SELECT status, COUNT(*) FROM appointments GROUP BY status;
```

### Redis

Access Redis:
```bash
docker exec -it studentska_redis redis-cli
```

Common commands:
```
ping                                      # Test connection
KEYS *                                    # List all keys
GET slot:lock:abc123                      # Get slot lock
ZRANGE waitlist:abc123 0 -1 WITHSCORES   # Get waitlist
FLUSHDB                                   # Clear all keys (development only!)
```

---

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_appointments.py::test_book_appointment

# Run with coverage report
pytest --cov=app --cov-report=html
```

### Frontend Tests (Phase 2)

```bash
# Jest + React Testing Library
npm test

# Watch mode
npm test -- --watch

# Coverage report
npm test -- --coverage
```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check Docker logs
docker-compose logs

# Check individual service
docker-compose logs studentska_fastapi

# Restart services
docker-compose restart
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check database exists
docker exec studentska_postgres psql -U postgres -l | grep studentska

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### Redis Connection Errors

```bash
# Test Redis connection
docker exec studentska_redis redis-cli ping
# Should return "PONG"
```

### Keycloak Issues

```bash
# Check Keycloak logs
docker logs studentska_keycloak

# Access Keycloak admin console
# http://localhost:8080/admin/master/console/
# admin / admin
```

---

## 📝 Code Style

### Backend (Python)

```bash
# Format with Black
black app/

# Sort imports with isort
isort app/

# Lint with pylint
pylint app/
```

### Frontend (TypeScript/React)

```bash
# Format with Prettier
npm run prettier

# Lint with ESLint
npm run lint

# Type check
npm run type-check
```

---

## 🚀 Deployment

### Production Build

```bash
# Backend
docker build -f backend/Dockerfile -t studentska-api:latest ./backend

# Frontend
docker build -f frontend/Dockerfile -t studentska-web:latest ./frontend
```

### Production Deployment

Use `docker-compose.prod.yml`:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 📚 Useful Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Next.js Documentation](https://nextjs.org/docs)
- [Keycloak Admin API](https://www.keycloak.org/docs/latest/server_admin/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

---

## 🆘 Getting Help

- Check `/memories/session/plan.md` for project planning details
- Review `docs/` folder for architecture and API specifications
- Check Docker logs for error messages
- Ask questions in project discussions

---

*Last updated: April 2026*
