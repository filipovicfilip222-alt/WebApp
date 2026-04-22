# GitHub Copilot — Plan Mode: Studentska Platforma

## ULOGA I KONTEKST

Ti si senior full-stack arhitekta koji planira razvoj **Platforme za upravljanje univerzitetskim konsultacijama i komunikacijom**. Tvoj zadatak je da kreirate detaljan, strukturiran razvojni plan pre nego što se napiše i jedna linija koda.

Projekat je **visoko-bezbedna, zatvorena intranet platforma** namenjena akademskim institucijama. Čitaj sledeća dva dokumenta u `docs/` direktorijumu kao **jedini source of truth**:

- `docs/PRD_Studentska_Platforma.md` — Specifikacija proizvoda, svi poslovni zahtevi i funkcionalnosti
- `docs/Arhitektura_i_Tehnoloski_Stek.md` — Odobrena tehnička arhitektura i razlozi za odabir svake tehnologije

**NE predlaži alternativne tehnologije.** Arhitektura je finalizovana i odobrena.

---

## TEHNOLOŠKI STEK (FIKSAN)

| Sloj | Tehnologija |
|------|-------------|
| Backend API | FastAPI (Python 3.12+) |
| Relaciona baza | PostgreSQL 16 + pgvector |
| Keš / Locking / Queues | Redis 7 |
| Frontend | Next.js 14 (App Router) + Tailwind CSS + Shadcn/ui |
| Autentifikacija / SSO | Keycloak (self-hosted) |
| File Storage | MinIO (self-hosted, S3-compatible) |
| Real-time | WebSockets (FastAPI native) |
| Kontejnerizacija | Docker + Docker Compose |
| Kalendar UI | FullCalendar (React) |

---

## ZADATAK: KREIRAJ KOMPLETAN RAZVOJNI PLAN

Generiši sledeće artefakte u Plan Mode-u. **Ne generišu se fajlovi sa kodom** — samo plan, struktura i specifikacije.

---

### 1. STRUKTURA PROJEKTA (Monorepo)

Predloži kompletnu folder strukturu monorepo projekta:

```
/
├── backend/          # FastAPI aplikacija
├── frontend/         # Next.js aplikacija  
├── infra/            # Docker, Keycloak, MinIO konfiguracije
├── docs/             # PRD i Arhitektura dokumenti
└── scripts/          # Pomocni skripti (seed, migrate, etc.)
```

Razradi svaki direktorijum do nivoa koji je dovoljan da developer počne rad bez pitanja.

---

### 2. BAZA PODATAKA — ER DIJAGRAM I ŠEMA

Na osnovu PRD-a, definiši sve tabele sa kolonama, tipovima podataka i relacijama. Obuhvati:

- `users` (sa RBAC ulogom: STUDENT, ASISTENT, PROFESOR, ADMIN)
- `professors` (profil, kabinet, zvanje, oblasti)
- `subjects` (predmeti, veza sa profesorima/asistentima)
- `availability_slots` (šabloni dostupnosti profesora, recurring pravila)
- `blackout_dates` (blokade dana)
- `appointments` (zakazani termini, status, tip: UZIVO/ONLINE)
- `appointment_participants` (grupne konsultacije, vođa + kolege)
- `waitlist` (lista čekanja po slotu)
- `files` (upload-ovani fajlovi vezani za appointment)
- `ticket_chat_messages` (in-app chat per terminu)
- `crm_notes` (privatne beleške profesora o studentima)
- `strike_records` (kazneni poeni)
- `faq_items` (FAQ na profilu profesora)
- `notifications` (in-app notifikacije)
- `audit_log` (admin impersonacija log)
- `canned_responses` (šabloni odgovora profesora)

Za svaku tabelu navedi: naziv kolone, tip, constraints (PK, FK, NOT NULL, UNIQUE, DEFAULT).

---

### 3. API SPECIFIKACIJA (OpenAPI-style)

Definiši sve FastAPI endpoint-e grupisane po modulima. Za svaki endpoint navedi:
- HTTP metod i putanju
- Ko ima pristup (RBAC uloga)
- Request body / query params (ključna polja)
- Response schema (ključna polja)
- Posebne napomene (Redis locking, WebSocket, background task itd.)

**Moduli:**

#### 3.1 Auth & Users (`/api/v1/auth/`)
- `GET /sso/redirect` — Redirect na Keycloak login
- `GET /sso/callback` — OAuth2 callback, kreira sesiju
- `POST /logout`
- `GET /me` — Trenutni korisnik + uloga

#### 3.2 Student Portal (`/api/v1/students/`)
- Pretraga profesora (sa filterima: ime, katedra, predmet, keyword)
- Profil profesora (sa FAQ, slobodnim slotovima)
- Zakazivanje termina (sa Redis pessimistic locking na slotu)
- Otkazivanje termina (24h pravilo)
- Waitlist prijava/odjava
- Moji termini (upcoming + history)

#### 3.3 Professor Portal (`/api/v1/professors/`)
- Upravljanje availability šablonima (CRUD recurring slots)
- Blackout datumi
- Lista pristiglih zahteva
- Odobravanje / odbijanje zahteva (manual + auto-approve konfiguracija)
- Delegiranje asistentu
- Šabloni odgovora (canned responses CRUD)
- CRM beleške o studentu
- FAQ menadžment

#### 3.4 Appointments (`/api/v1/appointments/`)
- Detalji termina
- In-app ticket chat (WebSocket endpoint)
- Upload fajlova (multipart, max 5MB, MinIO)
- Grupne konsultacije (tag kolega + potvrde)

#### 3.5 Admin Panel (`/api/v1/admin/`)
- CRUD korisnika
- Bulk import studenata (CSV)
- Impersonacija (sa audit logom)
- Upravljanje kaznenim poenima (pregled, skidanje blokade)
- Globalni broadcast (baner + email/push)

#### 3.6 Pretraga (`/api/v1/search/`)
- Google Programmable Search Engine proxy endpoint

#### 3.7 Notifikacije (`/api/v1/notifications/`)
- Lista notifikacija za korisnika
- Označavanje kao pročitano
- WebSocket kanal za real-time notifikacije

---

### 4. KEYCLOAK KONFIGURACIJA PLAN

Opiši šta treba konfigurisati u Keycloak-u:

- Realm podešavanja (naziv, token lifetime)
- Klijenti (FastAPI backend, Next.js frontend)
- Identity Providers (G-Suite OAuth2, Microsoft 365 OIDC)
- Realm Roles: `student`, `assistant`, `professor`, `admin`
- Role Mapper (kako se uloge prenose u JWT token)
- User Federation (LDAP / Active Directory connector opcija)

---

### 5. REDIS ARHITEKTURA PLAN

Definiši Redis key namespace i TTL za svaki use case:

| Namespace | Primer ključa | TTL | Opis |
|-----------|--------------|-----|------|
| `slot:lock:{slot_id}` | `slot:lock:abc123` | 30s | Pessimistic lock pri zakazivanju |
| `waitlist:{slot_id}` | `waitlist:abc123` | — | Sorted set (timestamp = score) |
| `session:{user_id}` | `session:usr_001` | 24h | WebSocket sesija |
| `strike:pending:{user_id}` | `strike:pending:usr_001` | — | Neplaćene kazne |

Navedi koje Redis data structure koristiti za svaki slučaj (String, Hash, Sorted Set, List, Pub/Sub).

---

### 6. RAZVOJNI PLAN PO FAZAMA (Sprint Plan)

Podeli razvoj na faze:

#### Faza 0 — Infrastruktura (Nedelja 1-2)
- Docker Compose setup (sve servise lokalno)
- Keycloak konfiguracija i SSO test
- MinIO bucket setup
- PostgreSQL migracije (Alembic)
- FastAPI skeleton sa health check endpoint-om
- Next.js skeleton sa Keycloak autentifikacijom

#### Faza 1 — MVP Core (Nedelja 3-6)
- Availability Engine (profesor kreira slotove)
- Student zakazivanje + Redis locking
- Notifikacije (email + in-app)
- Osnovna RBAC middleware
- Strike system automatizacija
- Waitlist logika

#### Faza 2 — Komunikacija i Admin (Nedelja 7-10)
- In-App Ticket Chat (WebSocket)
- CRM beleške
- Admin panel (CRUD, bulk import, impersonacija)
- Globalni broadcast
- Grupne konsultacije

#### Faza 3 — Polish i V2 Prep (Nedelja 11-14)
- Google Programmable Search integracija
- PWA manifest i service worker
- FullCalendar drag-and-drop UX optimizacija
- Canned responses UI
- Priprema pgvector šeme za RAG (V2)
- Performance testing i optimizacija

---

### 7. SIGURNOSNI ZAHTEVI — CHECKLIST

Generiši listu svih sigurnosnih zahteva koje developer mora implementirati:

- [ ] Sve rute zaštićene Keycloak JWT validacijom
- [ ] RBAC middleware — svaki endpoint proverava ulogu
- [ ] Rate limiting na zakazivanje (sprečavanje spam zahteva)
- [ ] File upload validacija (tip, veličina, malware scan opcija)
- [ ] Audit log za sve admin akcije (uključujući impersonaciju)
- [ ] CORS podešen samo za `frontend` origin
- [ ] HTTPS enforced (Nginx reverse proxy)
- [ ] Redis lock atomičnost (Lua skripte za test-and-set)
- [ ] SQL injection prevencija (SQLAlchemy ORM only, no raw queries)
- [ ] Sensitivi podaci (beleške, audit log) — row-level security u PostgreSQL

---

### 8. ENVIRONMENT VARIJABLE PLAN

Navedi sve potrebne `.env` varijable grupisane po servisu:

```
# FastAPI Backend
DATABASE_URL=
REDIS_URL=
KEYCLOAK_SERVER_URL=
KEYCLOAK_REALM=
KEYCLOAK_CLIENT_ID=
KEYCLOAK_CLIENT_SECRET=
MINIO_ENDPOINT=
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_BUCKET_NAME=
GOOGLE_PSE_API_KEY=
GOOGLE_PSE_CX=
SECRET_KEY=

# Next.js Frontend
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_KEYCLOAK_URL=
NEXT_PUBLIC_KEYCLOAK_REALM=
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=

# Keycloak
KC_DB_URL=
KC_DB_USERNAME=
KC_DB_PASSWORD=
KC_ADMIN=
KC_ADMIN_PASSWORD=
```

---

### 9. FRONTEND STRANICE I KOMPONENTE PLAN

Na osnovu PRD-a, definiši sve Next.js stranice (App Router) i ključne komponente:

**Stranice:**
- `/` — Landing / Redirect na login
- `/dashboard` — Student homepage (upcoming termini, notifikacije)
- `/search` — Pretraga profesora
- `/professor/[id]` — Profil profesora + kalendar + FAQ
- `/appointments/[id]` — Detalji termina + chat + fajlovi
- `/my-appointments` — Istorija termina studenta
- `/professor/dashboard` — Professor portal (inbox zahteva, kalendar)
- `/professor/settings` — Availability, canned responses, FAQ menadžment
- `/admin` — Admin panel

**Ključne komponente:**
- `<AvailabilityCalendar />` — FullCalendar integracija za profesore (drag-and-drop kreiranje slotova)
- `<BookingCalendar />` — FullCalendar za studente (read-only slobodni slotovi)
- `<AppointmentRequestForm />` — Forma za zakazivanje (tema, opis, fajl upload)
- `<TicketChat />` — WebSocket chat komponenta
- `<StrikeDisplay />` — Prikaz kaznenih poena studenta
- `<WaitlistButton />` — Prijava/odjava sa liste čekanja
- `<NotificationCenter />` — Dropdown sa notifikacijama
- `<BulkImportModal />` — CSV upload za admin
- `<AuditLogTable />` — Prikaz audit loga za admin

---

### 10. PITANJA ZA POJAŠNJENJE (Pre kodiranja)

Pre početka razvoja, razresi sledeće:

1. **Email servis**: Koji SMTP server/servis koristiti za automatske emailove (podsetnici, otkazivanja)? SendGrid, Postfix lokalno, ili fakultetski SMTP?
2. **Push notifikacije**: Da li PWA push notifikacije (Web Push API) treba implementirati u MVP-u ili samo email + in-app?
3. **Vremenska zona**: Jedinstvena timezone za ceo sistem ili per-korisnik?
4. **Google PSE**: Da li je API ključ već obezbeđen ili treba biti deo setup procesa?
5. **Kapacitet**: Koliko simultanih korisnika se očekuje (za Redis pool i DB connection pool sizing)?
6. **Backup strategija**: Ko je odgovoran za PostgreSQL i MinIO backup? (Devops tim ili deo applikacije?)
7. **Mobile app**: PWA je dovoljna za MVP, ili paralelno treba planirati React Native wrapper?

---

## FORMAT ODGOVORA

Odgovori na sve sekcije (1-10) sa maksimalnom preciznošću. Koristi Markdown tabele, code blokove i liste. Svaka sekcija mora biti dovoljno detaljna da senior developer može početi implementaciju bez dodatnih pitanja.

**Jezik odgovora:** Srpski (tehnički termini na engleskom)
