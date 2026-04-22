# Studentska Platforma — Razvoj u Toku

## 📋 Pregled Projekta

Platforma za upravljanje univerzitetskim konsultacijama i komunikacijom.

**Status:** Phase 0 (Infrastruktura) ✅ KOMPLETAN  
**Verzija:** 1.0.0-dev  
**Tehnološki Stek:** FastAPI + PostgreSQL + Redis + Next.js + Keycloak

---

## 🚀 Phase 0 — Infrastruktura (KOMPLETAN)

### ✅ Kreirano:

1. **Docker Compose** — Svi servisi (postgres, redis, keycloak, fastapi, next.js, minio, celery)
2. **PostgreSQL Init** — Sve tabele sa enums, indexes, pgvector ekstenzijom
3. **Keycloak Realm Config** — Realm setup sa client-ima i identity providers-ima
4. **FastAPI Skeleton** — Main.py, config.py, database setup, health endpoint
5. **Next.js Skeleton** — Layout, landing page, package.json, tailwind setup
6. **Requirements** — Python zavisnosti (FastAPI, SQLAlchemy, Celery, itd.)
7. **Dockerfiles** — Multi-stage builds za Backend i Frontend
8. **.env Template** — Svi env variables sa default vrednostima

### 📂 Struktura Direktorijuma

```
studentska-platforma/
├── backend/                    # FastAPI aplikacija
│   ├── app/
│   │   ├── main.py            # App factory
│   │   ├── config.py          # Settings
│   │   ├── db/                # Database setup
│   │   ├── models/            # SQLAlchemy ORM
│   │   ├── schemas/           # Pydantic DTO-ovi
│   │   ├── services/          # Business logic
│   │   ├── tasks/             # Celery background jobs
│   │   ├── api/v1/            # API endpoints (placeholder)
│   │   └── utils/             # Helpers
│   ├── migrations/            # Alembic
│   ├── tests/                 # Unit/integration tests
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                  # Next.js aplikacija
│   ├── src/
│   │   ├── app/              # App Router (pages)
│   │   ├── components/       # React komponente (placeholder)
│   │   ├── hooks/            # Custom hooks (placeholder)
│   │   ├── services/         # API client (placeholder)
│   │   ├── lib/              # Utilities (placeholder)
│   │   └── styles/           # Tailwind CSS
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── next.config.js
│   └── Dockerfile
│
├── infra/                     # DevOps & Infrastructure
│   ├── postgres/
│   │   └── init.sql          # Database schema sa pgvector
│   ├── keycloak/
│   │   └── imports/
│   │       └── realm-config.json
│   ├── nginx/                # Reverse proxy (Phase 3)
│   ├── redis/                # Redis config (u Docker)
│   └── minio/                # MinIO config (u Docker)
│
├── scripts/
│   ├── seed_dev_data.py      # Development data seeding
│   ├── migrate_db.sh         # Alembic migrations
│   ├── backup_postgres.sh    # Backup script (Phase 0)
│   └── load_test.py          # Load testing (Phase 3)
│
├── docs/                      # Dokumentacija
│   ├── PRD_Studentska_Platforma.md
│   ├── Arhitektura_i_Tehnoloski_Stek.md
│   └── DEVELOPMENT.md
│
├── docker-compose.yml         # Svi servisi lokalno
├── .env.example              # Template za environment varijable
├── .gitignore
└── README.md                 # Ovaj fajl
```

---

## 🛠️ Kako Početi (Local Development)

### Preduslov:
- Docker Desktop (ili Docker + Docker Compose)
- Git
- Python 3.12+ (opciono za direktan development)
- Node.js 20+ (opciono za direktan development)

### 1. Kloniranje i Setup

```bash
cd studentska-platforma
cp .env.example .env
```

### 2. Pokrećanje Docker Compose-a

```bash
docker-compose up -d
```

**Cekaj da se servisi pokrenu** (~30 sekundi):
- ✅ PostgreSQL: http://localhost:5432
- ✅ Redis: localhost:6379
- ✅ Keycloak: http://localhost:8080
- ✅ FastAPI: http://localhost:8000
- ✅ Next.js: http://localhost:3000
- ✅ MinIO: http://localhost:9001 (minio:minioadmin)

### 3. Verifikacija

```bash
# Health check FastAPI
curl http://localhost:8000/health
# {"status":"ok","environment":"development"}

# Keycloak login
open http://localhost:8080
# Username: admin
# Password: admin (sa .env)

# Next.js frontend
open http://localhost:3000
```

---

## 📊 Servisi

| Servis | Port | URL | Kredencijali |
|--------|------|-----|--------------|
| PostgreSQL | 5432 | `postgres://postgres:postgres@localhost/studentska_platforma` | postgres / postgres |
| Redis | 6379 | `redis://localhost:6379` | — |
| Keycloak | 8080 | http://localhost:8080 | admin / admin |
| FastAPI | 8000 | http://localhost:8000 | — |
| Next.js | 3000 | http://localhost:3000 | — |
| MinIO (API) | 9000 | http://localhost:9000 | minioadmin / minioadmin |
| MinIO (UI) | 9001 | http://localhost:9001 | minioadmin / minioadmin |

---

## 🔑 Keycloak Setup

Realm je automatski importovan pri startup-u.

**Realm Roles:**
- `student`
- `asistent`
- `profesor`
- `admin`

**Clients:**
- `fakultet-backend` (FastAPI, confidential)
- `fakultet-frontend` (Next.js, public)

---

## 📚 Database Schema

Sve tabele su kreirane sa `docker-compose up`:
- `users`, `student_profiles`, `professor_profiles`
- `subjects`, `subject_staff`
- `availability_slots`, `blackout_dates`
- `appointments`, `appointment_participants`, `appointment_files`
- `ticket_chat_messages`, `waitlist`
- `crm_notes`, `strike_records`
- `faq_items`, `canned_responses`
- `notifications`, `audit_log`

Indeksi su optimizovani za glavne queries.

---

## 🧪 Testiranje (Phase 0)

```bash
# Backend health check
curl -X GET http://localhost:8000/health

# Frontend landing page
curl -X GET http://localhost:3000
```

---

## 📝 Sledeće Korake (Phase 1)

- [ ] Kreiraj API endpoint-e za zakazivanje (`POST /api/v1/students/appointments`)
- [ ] Implementiraj Redis pessimistic locking za sprečavanje double-booking-a
- [ ] Setup Alembic migracije sa verzionisanjem
- [ ] Kreiraj seed data sa 5 profesora i 50 studenata
- [ ] Implementiraj Keycloak JWT validaciju sa middleware-om
- [ ] Kreiraj UI za pretragu profesora i zakazivanje

---

## 🔐 Bezbednost

Konfigurisano za development:
- CORS: `localhost:3000`, `localhost:8000`
- JWT: Keycloak SSO
- Database: Lokalni (ne produksioni kredencijali)
- Secrets: `.env` nije commitovan (.gitignore)

**Za produkciju:**
- Promeni sve secret-e u `.env`
- Setuj HTTPS sa pravim SSL certifikatima
- Konfiguruj database backups
- Setuj monitoring i logging

---

## 📞 Kontakt i Support

Za pitanja o development plan-u, pogledaj `/memories/session/plan.md`.

---

*Generated by AI Architect — April 2026*
