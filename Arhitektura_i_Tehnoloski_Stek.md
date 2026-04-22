# Arhitektura i Tehnološki Stek
## Platforma za upravljanje univerzitetskim konsultacijama i komunikacijom

**Status:** Odobreno ✅  
**Verzija:** 1.1  
**Poslednja izmena:** April 2025  

> Ovaj dokument definiše **finalnu, odobrenu** tehničku arhitekturu. Svaka tehnološka odluka je doneta uz analizu alternativa i **ne podleže ponovnom razmatranju** tokom razvoja MVP-a.

---

## Sadržaj

1. [Pregled Arhitekture](#1-pregled-arhitekture)
2. [Backend API — FastAPI (Python)](#2-backend-api--fastapi-python)
3. [Relaciona Baza — PostgreSQL](#3-relaciona-baza--postgresql)
4. [Keš i State Management — Redis](#4-keš-i-state-management--redis)
5. [Frontend i PWA — Next.js](#5-frontend-i-pwa--nextjs)
6. [Autentifikacija i SSO — Keycloak](#6-autentifikacija-i-sso--keycloak)
7. [File Storage — MinIO](#7-file-storage--minio)
8. [Deployment Arhitektura](#8-deployment-arhitektura)
9. [Dijagram Komunikacije između Servisa](#9-dijagram-komunikacije-između-servisa)

---

## 1. Pregled Arhitekture

```
┌─────────────────────────────────────────────────────────┐
│                    KLIJENTI (Browser / PWA)              │
│              Next.js 14 + Tailwind + Shadcn/ui           │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS / WSS
┌────────────────────────▼────────────────────────────────┐
│                   Nginx Reverse Proxy                    │
│              (SSL Termination, CORS, Rate Limit)         │
└────┬───────────────────┬────────────────────────────────┘
     │                   │
┌────▼──────┐    ┌────────▼──────────────────────────────┐
│ Keycloak  │    │         FastAPI Backend                │
│ (SSO/RBAC)│◄───│   REST API + WebSocket endpoints       │
└───────────┘    └────┬──────────┬──────────┬────────────┘
                      │          │           │
              ┌───────▼──┐ ┌─────▼───┐ ┌───▼─────┐
              │PostgreSQL│ │  Redis  │ │  MinIO  │
              │+ pgvector│ │ (Cache) │ │ (Files) │
              └──────────┘ └─────────┘ └─────────┘
```

**Princip arhitekture:** API-first, skalabilna, asinhrona, sa punom podrškom za buduću AI/RAG integraciju bez refaktorisanja.

---

## 2. Backend API — FastAPI (Python)

**Odabrana verzija:** FastAPI 0.111+ sa Python 3.12+

### Razlozi za odabir

#### ✅ AI-Ready (Prioritet za V2 RAG)
Python je apsolutni standard za razvoj veštačke inteligencije. Prelaz na V2 RAG sistem (LangChain, LlamaIndex, pgvector) biće **nativna integracija unutar istog ekosistema** — bez podizanja zasebnih mikroservisa ili language bridge-a.

#### ✅ Performanse i Asinhronost
FastAPI je izgrađen na **Starlette** i **Pydantic** bibliotekama, što ga čini jednim od najbržih Python web framework-a. `async/await` model je savršen za I/O-heavy operacije:
- Upiti bazi podataka (async SQLAlchemy)
- Redis operacije (aioredis)
- MinIO upload/download
- Google PSE API pozivi

#### ✅ Auto-generisana OpenAPI Dokumentacija
Swagger UI i ReDoc se automatski generišu iz Pydantic šema, što eliminiše ručno pisanje dokumentacije i ubrzava sinhronizaciju između frontend i backend timova.

#### ✅ Native WebSocket Podrška
FastAPI nativno podržava WebSocket endpoint-e — ključno za In-App Ticket Chat i real-time notifikacije.

### Ključne biblioteke

| Biblioteka | Namena |
|-----------|--------|
| `sqlalchemy[asyncio]` + `asyncpg` | Async ORM za PostgreSQL |
| `alembic` | Migracije baze |
| `redis[asyncio]` (aioredis) | Async Redis klijent |
| `minio` | MinIO S3-compatible klijent |
| `python-jose` | JWT validacija Keycloak tokena |
| `celery` + `redis` | Background taskovi (email slanje, strike provere) |
| `pydantic-settings` | Type-safe env varijable |
| `pytest-asyncio` | Async testovi |

### Zašto NE alternative?

| Alternativa | Razlog odbijanja |
|-------------|-----------------|
| **Spring Boot (Java)** | Zahteva znatno više boilerplate koda i otežava AI integraciju — za V2 bi bio potreban zasebni Python mikroservis |
| **Django** | Sinhroni i monolitni dizajn; FastAPI nudi bolje performanse za API-first arhitekturu |
| **Node.js / Express** | Nema nativnu prednost u AI/ML ekosistemu; Python je industrijski standard za AI |
| **Go (Gin/Echo)** | Odlične performanse, ali minimalan AI/ML ekosistem; otežava V2 implementaciju |

---

## 3. Relaciona Baza — PostgreSQL

**Odabrana verzija:** PostgreSQL 16 sa `pgvector` ekstenzijom

### Razlozi za odabir

#### ✅ ACID Usklađenost za Kompleksne Relacije
Sistem zakazivanja zahteva **strogu konzistentnost podataka** kroz kompleksne relacije:
```
Student → Appointment → Slot → Professor → Subject → Assistant
```
PostgreSQL garantuje da neće doći do korupcije podataka kod paralelnih transakcija (npr. dva studenta istovremeno zakazuju isti termin).

#### ✅ pgvector — Ključni Razlog za Odabir
`pgvector` ekstenzija omogućava čuvanje **vektorskih embedding-a direktno u PostgreSQL**. Kada se uvede V2 RAG sistem:
- Nema potrebe za zasebnim vektorskim bazama (Pinecone, Weaviate, Chroma)
- Embedding-i žive pored relacijskih podataka — jednostavniji upiti, manji infrastrukturni overhead
- Semantička pretraga dokumenata fakulteta direktno iz iste baze

#### ✅ Napredni Tipovi Podataka
- `JSONB` — fleksibilno čuvanje konfiguracionih podataka (recurring rules, notification preferences)
- `ARRAY` tipovi — lista tagova, oblasti interesovanja profesora
- `TSRANGE` / `TSTZRANGE` — nativna podrška za vremenske intervale (idealno za availability slots)
- Full-text search sa srpskim locale-om

#### ✅ Row-Level Security (RLS)
Nativna PostgreSQL funkcionalnost koja omogućava da privatne CRM beleške i audit logovi budu zaštićeni na nivou baze — čak i ako dođe do greške u aplikacionom sloju.

### Zašto NE alternative?

| Alternativa | Razlog odbijanja |
|-------------|-----------------|
| **MongoDB (NoSQL)** | Nije pogodan za duboke relacije i ACID transakcije; kompleksni JOIN upiti su spori |
| **MySQL** | Nema pgvector podršku; slabija podrška za napredne tipove podataka |
| **SQLite** | Ne podržava konkurentne write operacije; nije za produkciju |
| **Supabase** | SaaS rešenje — narušava data sovereignty zahteve fakulteta |

---

## 4. Keš i State Management — Redis

**Odabrana verzija:** Redis 7 (self-hosted)

### Razlozi za odabir i Use Cases

#### ✅ Sprečavanje Double Booking (Race Conditions)
Ovo je **najkritičniji use case** u sistemu. Kada student klikne na slobodan slot:
1. Redis **atomičnim SET NX** operacijom (Lua skripta) zaključava slot na 30 sekundi
2. Tokom tih 30 sekundi, drugi studenti vide slot kao "zauzet"
3. Ako student odustane ili validacija padne, lock ističe automatski
4. Ako student potvrdi, zapis se pravi u PostgreSQL i lock se otpušta

Ova arhitektura eliminuje potrebu za DB-level pessimistic locking koji bi usporavao bazu.

#### ✅ Waitlist Queue Management
Redis **Sorted Sets** su idealni za waitlist:
- Score = Unix timestamp prijave
- `ZPOPMIN` automatski vraća studenta koji čeka najduže
- Atomičan pop + push za siguran transfer između liste čekanja i confirmed termina

#### ✅ WebSocket Sesije i Pub/Sub
- In-App Ticket Chat koristi Redis **Pub/Sub** za razmenu poruka između WebSocket konekcija
- Ako su pokrenute multiple instance FastAPI servera, Redis osigurava da poruka stigne do pravog WebSocket klijenta bez obzira na koji server je konektovan

#### ✅ Background Task Queue (Celery Broker)
- Redis kao Celery broker za:
  - Slanje email notifikacija (async, ne blokira API response)
  - Automatska provera no-show termina (cron job svakih 30 minuta)
  - Procesiranje waitlist notifikacija

### Redis Key Namespace

| Namespace | Tip | TTL | Opis |
|-----------|-----|-----|------|
| `slot:lock:{slot_id}` | String | 30s | Pessimistic lock pri zakazivanju |
| `waitlist:{slot_id}` | Sorted Set | ∞ | Lista čekanja (score = timestamp) |
| `chat:session:{appointment_id}` | Hash | 25h | WebSocket sesije za chat |
| `notif:unread:{user_id}` | Counter | ∞ | Broj nepročitanih notifikacija |
| `strike:check:{appointment_id}` | String | 90min | Scheduled no-show provera |

### Zašto NE alternative?

| Alternativa | Razlog odbijanja |
|-------------|-----------------|
| **In-memory (Python dict)** | Ne skalira — lokalna memorija jednog servera ne zna šta je zaključano na drugom pri load balancingu |
| **PostgreSQL SKIP LOCKED** | Moguće rešenje za locking, ali sporo za high-frequency operacije; PostgreSQL nije dizajniran za keš |
| **Memcached** | Nema Pub/Sub, Sorted Sets ni perzistenciju — premali feature set |

---

## 5. Frontend i PWA — Next.js

**Odabrana verzija:** Next.js 14 (App Router) sa Tailwind CSS

### Razlozi za odabir

#### ✅ App Router i Server Components
Next.js 14 App Router omogućava **selektivni SSR** — profili profesora i statični sadržaj se renderuju na serveru (bolje SEO i initial load), dok interaktivni kalendar i chat rade kao Client Components.

#### ✅ PWA Podrška
Next.js ima odlične alate za PWA kompilaciju (`next-pwa`):
- Service Worker za offline caching
- Web App Manifest za instalaciju na telefon
- Web Push API za push notifikacije
- Studenti i profesori instaliraju aplikaciju direktno iz browsera — **bez App Store / Play Store procesa odobravanja i troškova**

#### ✅ Bogat Ekosistem za Kalendar
**FullCalendar** je najnaprednije rešenje za kompleksne kalendare i najbolje radi unutar React ekosistema:
- Drag-and-drop kreiranje slotova za profesore
- Month/Week/Day prikazi
- Resource view (više profesora istovremeno za admina)
- Real-time update via WebSocket

#### ✅ Shadcn/ui Komponente
Shadcn/ui je odabran umesto Material UI ili Ant Design jer:
- Komponente se **kopiraju u projekat** (nisu dependency) — potpuna kontrola
- Odlična integracija sa Tailwind CSS
- Accessibility-first dizajn

### Ključne biblioteke

| Biblioteka | Namena |
|-----------|--------|
| `@fullcalendar/react` | Kalendarski UI za profesore i studente |
| `shadcn/ui` | UI komponente (Dialog, Form, Table, etc.) |
| `tailwindcss` | Utility-first CSS |
| `next-auth` + Keycloak adapter | Upravljanje SSO sesijom na frontendu |
| `react-query` (TanStack Query) | Server state management, caching API poziva |
| `react-hook-form` + `zod` | Forme sa validacijom |
| `socket.io-client` | WebSocket klijent za chat i notifikacije |
| `next-pwa` | PWA konfiguracija i service worker |
| `react-dropzone` | Drag-and-drop file upload UI |

### Zašto NE alternative?

| Alternativa | Razlog odbijanja |
|-------------|-----------------|
| **Vite/CRA (čist React)** | Nema ugrađen SSR, PWA manifest mora ručno, sporije initial loading |
| **Angular** | Strmija krivulja učenja, sporiji time-to-market za MVP |
| **Vue.js / Nuxt** | Manji ekosistem za kalendarke biblioteke; React je industrijski standard |
| **SvelteKit** | Odlično, ali manji ekosistem — FullCalendar je primarno React |

---

## 6. Autentifikacija i SSO — Keycloak

**Odabrana verzija:** Keycloak 24+ (self-hosted, on-premise)

### Razlozi za odabir

#### ✅ Enterprise SSO Integracija
Keycloak se nativno integriše sa:
- **Active Directory / LDAP** (User Federation — automatska sinhronizacija naloga)
- **Microsoft 365** (SAML 2.0 ili OIDC)
- **G-Suite** (Google OAuth 2.0)
- Ovo su tačno oni sistemi koje fakulteti već koriste

#### ✅ Data Sovereignty — On-Premise
Keycloak se pokreće **na internim serverima fakulteta**:
- Korisnički akreditivi nikada ne napuštaju mrežu institucije
- Usklađenost sa GDPR i internim pravilnicima o zaštiti podataka studenata
- Potpuna kontrola nad token lifetime, session policies i audit logovima autentifikacije

#### ✅ Ugrađeni RBAC
Keycloak nativno upravlja Realm Roles:
- `student`, `assistant`, `professor`, `admin`
- Role se mapiraju u JWT token claims
- FastAPI middleware čita uloge direktno iz tokena — nema potrebe za zasebnom tabelom permisija

#### ✅ Protokol Podrška
- **OpenID Connect (OIDC)** za web aplikacije
- **OAuth 2.0** za API pristup
- **SAML 2.0** kao fallback za starije enterprise sisteme

### Zašto NE alternative?

| Alternativa | Razlog odbijanja |
|-------------|-----------------|
| **Auth0** | SaaS/Cloud — korisnički podaci napuštaju mrežu institucije; narušava Data Sovereignty |
| **Firebase Auth** | Google Cloud zavisnost; iste probleme kao Auth0 |
| **Custom JWT (FastAPI)** | Pisanje sopstvenog SSO sistema je bezbednosni rizik i gubljenje vremena na rešen problem |
| **Okta** | Komercijalana SaaS licenca; isti problemi kao Auth0 |

---

## 7. File Storage — MinIO

**Odabrana verzija:** MinIO AGPL (self-hosted)

### Razlozi za odabir

#### ✅ Amazon S3 Kompatibilni API
MinIO koristi isti API kao Amazon S3:
- Kod za upload/download fajlova (studentski radovi, PDF-ovi, kod) je standardizovan
- Ako institucija u budućnosti odluči da migrira na AWS S3, promene koda su minimalne
- Sve Python S3 biblioteke (`boto3`, `minio`) rade bez izmena

#### ✅ Self-Hosted — Fajlovi Ostaju na Kampusu
MinIO se instalira na serverima fakulteta:
- Studentski radovi, skripte i PDF dokumenti **nikada ne napuštaju mrežu**
- Usklađenost sa politikama intelektualne svojine i privatnosti

#### ✅ Performanse
- MinIO je optimizovan za large-scale object storage
- Direktni pre-signed URL-ovi za download — fajlovi se ne "prolaze" kroz FastAPI server, čime se eliminišu uska grla

### Bucket Struktura

```
minio-buckets/
├── appointment-files/      # Upload-ovani fajlovi po terminu
│   └── {appointment_id}/
│       └── {filename}
├── professor-avatars/      # Profilne slike profesora
└── bulk-imports/           # CSV fajlovi za bulk import (privremeno)
```

### Zašto NE alternative?

| Alternativa | Razlog odbijanja |
|-------------|-----------------|
| **Amazon S3** | Cloud/SaaS — fajlovi napuštaju mrežu institucije |
| **BLOB u PostgreSQL** | Anti-pattern — drastično usporava bazu, otežava backup |
| **Lokalni fajl sistem** | Ne skalira — fajl sačuvan na jednom serveru nije dostupan sa drugog pri load balancingu |
| **Nextcloud** | Nije S3-kompatibilan; nema direktnu integraciju sa Python S3 SDK |

---

## 8. Deployment Arhitektura

### Docker Compose (Lokalni Razvoj i Produkcija)

```yaml
services:
  nginx:          # Reverse proxy, SSL termination
  fastapi:        # Backend API (može biti više replika)
  celery-worker:  # Background tasks (email, cron)
  nextjs:         # Frontend
  postgres:       # Baza podataka
  redis:          # Keš, queue, pub/sub
  keycloak:       # SSO server
  minio:          # Object storage
```

### Mrežna Izolacija
- Svi servisi komuniciraju unutar **Docker interne mreže**
- Spolja su dostupni samo **Nginx** (port 443) i **Keycloak** (port 8443)
- MinIO, PostgreSQL i Redis **nisu izloženi** van Docker mreže

### Skaliranje
- FastAPI i Celery Worker se skaliraju horizontalno (više Docker replika)
- PostgreSQL: Primary + Read Replica (za reporting upite admina)
- Redis: Sentinel konfiguracija za high availability

---

## 9. Dijagram Komunikacije između Servisa

```
[Browser / PWA]
      │
      │ HTTPS (REST + WebSocket)
      ▼
   [Nginx]
      │
      ├──► [Next.js SSR]      (stranice, SEO)
      │
      └──► [FastAPI API]
               │
               ├──► [Keycloak]    JWT validacija (per-request)
               │
               ├──► [PostgreSQL]  Persistentni podaci
               │        └──► pgvector (V2 RAG)
               │
               ├──► [Redis]       Locking, Queue, Pub/Sub, Cache
               │        └──► Celery Worker (email, cron)
               │
               └──► [MinIO]       File upload/download (pre-signed URLs)
```

---

## Zaključak

Odabrani stek:

| | |
|-|-|
| **Backend** | FastAPI (Python 3.12) |
| **Baza** | PostgreSQL 16 + pgvector |
| **Keš** | Redis 7 |
| **Frontend** | Next.js 14 + Tailwind + Shadcn/ui + FullCalendar |
| **Auth** | Keycloak 24 (on-premise) |
| **Storage** | MinIO (self-hosted, S3-compatible) |
| **Deployment** | Docker + Docker Compose + Nginx |

Ovaj stek predstavlja optimalan balans između:
- **Visoke sigurnosti** (Data Sovereignty, RBAC, on-premise sve komponente)
- **Performansi** (async arhitektura, Redis locking, pre-signed file URLs)
- **Razvojne brzine** (auto-generisana dokumentacija, Shadcn/ui, TypeScript)
- **Budućnosti** (pgvector + Python = nativna AI/RAG podrška u V2)

---

*Dokument je deo `docs/` foldera projekta i služi kao jedini source of truth za tehničku arhitekturu.*
