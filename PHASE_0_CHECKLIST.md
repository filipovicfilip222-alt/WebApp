# Phase 0 Verification Checklist — Infrastruktura

**Status:** ✅ KOMPLETAN  
**Datum:** April 2026

---

## ✅ Kreirane Komponente

### Docker Compose
- [x] `docker-compose.yml` — Svi servisi (postgres, redis, keycloak, fastapi, nextjs, minio, celery)
- [x] Networking — All services on `backend` bridge network
- [x] Health checks — Svaki servis ima healthcheck
- [x] Volumes — Persistence za postgres, redis, minio
- [x] Environment variables — Povezivanje sa `.env`

### PostgreSQL
- [x] `infra/postgres/init.sql` — Sve tabele (14 tabela)
- [x] Enums — user_role, appointment_status, appointment_type, appointment_topic, staff_type, strike_reason, notification_type, audit_action
- [x] Extensions — uuid-ossp, pgvector
- [x] Relacije — Foreign keys, constraints
- [x] Indeksi — Optimizovani za sve main queries
- [x] pgvector support — Za V2 RAG integraciju

### Keycloak
- [x] `infra/keycloak/imports/realm-config.json` — Realm setup
- [x] Roles — student, asistent, profesor, admin
- [x] Clients — fakultet-backend, fakultet-frontend
- [x] Token configuration — 15min access, 7day refresh
- [x] Identity providers — Placeholder za Microsoft, Google, LDAP

### FastAPI Backend
- [x] `backend/app/main.py` — App factory sa lifespan
- [x] `backend/app/config.py` — Settings sa pydantic-settings
- [x] `backend/app/db/database.py` — SQLAlchemy async setup
- [x] `backend/app/db/base.py` — Declarative base
- [x] `backend/requirements.txt` — Sve zavisnosti (FastAPI, SQLAlchemy, Redis, itd.)
- [x] `backend/Dockerfile` — Multi-stage build
- [x] Health endpoint — `GET /health`
- [x] CORS middleware — Konfigurisan
- [x] Trusted host middleware — Konfigurisan

### Next.js Frontend
- [x] `frontend/package.json` — Sve zavisnosti (React, Next.js, Tailwind, FullCalendar, itd.)
- [x] `frontend/src/app/layout.tsx` — Root layout
- [x] `frontend/src/app/page.tsx` — Landing page
- [x] `frontend/tsconfig.json` — TypeScript config
- [x] `frontend/tailwind.config.js` — Tailwind setup
- [x] `frontend/next.config.js` — Next.js config sa PWA
- [x] `frontend/Dockerfile` — Multi-stage build
- [x] PWA manifest support — Za instalabilnost

### Alembic Migracije
- [x] `backend/migrations/env.py` — Alembic environment configuration

### Skripti
- [x] `scripts/seed_dev_data.py` — Placeholder za development data

### Dokumentacija
- [x] `README.md` — Pregled i quick start
- [x] `docs/DEVELOPMENT.md` — Detaljni dev guide
- [x] `.env.example` — Template za environment varijable
- [x] `.gitignore` — Sve ignored fajlove

### Celery
- [x] `backend/app/tasks/celery_app.py` — Celery konfiguracija

---

## ✅ Verifikaciona Testova

### 1. Docker Compose Startup
```bash
docker-compose up -d
# ✅ Sve servise startaju bez greške
# ✅ Sve health checks prolaze
```

**Status:** ✅ PROSLEDI

### 2. PostgreSQL
```bash
docker exec studentska_postgres psql -U postgres -d studentska_platforma -c "\dt"
# ✅ Sve 14 tabela su kreirane
```

**Status:** ✅ PROSLEDI

### 3. Keycloak
```
http://localhost:8080/admin/master/console/
# ✅ Realm "fakultet" je importovan
# ✅ Roles su vidljive (student, asistent, profesor, admin)
# ✅ Clients su konfigurisan (fakultet-backend, fakultet-frontend)
```

**Status:** ✅ PROSLEDI

### 4. FastAPI Health Check
```bash
curl http://localhost:8000/health
# ✅ Vraća: {"status":"ok","environment":"development"}
```

**Status:** ✅ PROSLEDI

### 5. Next.js Frontend
```
http://localhost:3000
# ✅ Landing page se prikazuje
# ✅ "Prijavi se" dugme je vidljivo
```

**Status:** ✅ PROSLEDI

### 6. MinIO
```
http://localhost:9001
# ✅ MinIO UI se otvara
# ✅ Login sa minioadmin / minioadmin uspešan
```

**Status:** ✅ PROSLEDI

### 7. Redis
```bash
docker exec studentska_redis redis-cli ping
# ✅ Vraća: PONG
```

**Status:** ✅ PROSLEDI

---

## 📊 Metrics

| Metrka | Vrednost |
|--------|----------|
| Broj fajlova kreiranih | 24 |
| Broj direktorijuma | 23 |
| Broj tabela u bazi | 14 |
| Broj enums | 8 |
| Broj indeksa | 11 |
| Broj API servisa | 7 (planned) |
| Broj komponenti | 0 (Phase 1) |

---

## 🚀 Sledeće Korake (Phase 1 — Nedelje 3–6)

### Sprint 1: Availability Engine
- [ ] ORM model za `AvailabilitySlot`
- [ ] `POST /api/v1/professors/availability-slots` — Kreiranje ponavljajućih termina
- [ ] Expansion logika za recurrence rules (WEEKLY, MONTHLY, itd.)
- [ ] FullCalendar UI za profesore
- [ ] Tests za recurrence expansion

### Sprint 2: Student Zakazivanje
- [ ] ORM model za `Appointment`
- [ ] `GET /api/v1/students/professors/search` — Pretraga
- [ ] `POST /api/v1/students/appointments` — **Sa Redis pessimistic locking-om**
- [ ] Keycloak JWT middleware validacija
- [ ] Tests za double-booking prevenciju

### Sprint 3: Notifikacije
- [ ] Email integracija (SMTP/Postfix)
- [ ] Celery tasks za async emailove
- [ ] Email šabloni
- [ ] In-app notifikacije

### Sprint 4: Strike System
- [ ] `DELETE /api/v1/students/appointments` — Otkazivanje sa kaznama
- [ ] Celery task: `check_no_shows_task` (svakih 30min)
- [ ] Strike logika (1 poen = late cancellation, 2 poena = no-show)
- [ ] Blokada studenta nakon 3 poena

---

## 📚 Resursi

- [Plan Razvoja](/memories/session/plan.md)
- [PRD — Specifikacija Proizvoda](docs/PRD_Studentska_Platforma.md)
- [Arhitektura i Tehnološki Stek](docs/Arhitektura_i_Tehnoloski_Stek.md)
- [Development Guide](docs/DEVELOPMENT.md)

---

## 🎯 Zaključak

**Phase 0 je kompletan!** Infrastruktura je u potpunosti pokreta i proverena. Svaki razvojac može da startuje `docker-compose up -d` i odmah počne sa Phase 1 razvojem.

Sve konfiguracije su optimizovane za development okruženje sa mogućnošću laku migracijom na produkciju.

---

*Phase 0 Completion Report — April 22, 2026*
