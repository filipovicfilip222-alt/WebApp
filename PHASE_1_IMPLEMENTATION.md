# Phase 1 — MVP Core Implementation

**Status:** ✅ COMPLETE (Sprint 1-4 Foundation)

**Duration:** Weeks 3–6 (Nedelje 3–6)

## Overview

Phase 1 establishes the core API functionality for appointment booking, availability management, strike system, and notifications. This phase delivers the Minimum Viable Product (MVP) that allows professors to publish availability slots and students to request/book consultations.

## Architecture

```
FastAPI Backend
├── Models (SQLAlchemy ORM) — 14 tables with relationships
├── Schemas (Pydantic) — Request/response validation
├── Services — Business logic
│   ├── auth.py — Keycloak JWT integration
│   ├── availability.py — Slot expansion & recurrence
│   ├── appointment.py — Booking & strike detection
│   ├── redis_service.py — Pessimistic locking
│   ├── notification.py — User notifications
├── Routes (FastAPI) — REST endpoints
│   ├── appointments.py — Create/approve/cancel
│   ├── availability.py — Manage/search slots
│   ├── users.py — Profile management
│   ├── notifications.py — In-app notifications
│   ├── strikes.py — Admin strike management
└── Tasks (Celery) — Background jobs
    ├── send_email_notification — Email delivery
    ├── detect_no_shows — Strike automation
    ├── process_waitlist — Waitlist fulfillment
    ├── send_appointment_reminders — 24h before
    └── expire_strikes — Auto-removal after 30d
```

## What Was Built

### 1. Database Models (14 Tables)

```python
# Core entities
User              # Keycloak integration with roles
StudentProfile    # Student-specific data (strikes, blocks)
ProfessorProfile  # Professor metadata (office, title, bio)

# Availability & Appointments
AvailabilitySlot  # Recurring professor slots
BlackoutDate      # Professor unavailability (sick, conference)
Appointment       # Consultation bookings
AppointmentParticipant  # Group consultations

# Business Logic
StrikeRecord      # Discipline strikes (late cancel, no-show)
Waitlist          # Queue for full slots
CRMNote           # Private professor notes
Notification      # User notifications

# Meta
AuditLog          # Admin action tracking
FAQItem, CannedResponse  # Professor self-service templates
```

### 2. Authentication & Authorization

**Keycloak Integration:**
- JWT token validation middleware (`get_current_user`)
- Role-based access control (RBAC) via `realm_access.roles`
- 4 roles: STUDENT, ASISTENT, PROFESOR, ADMIN

**Example Usage:**
```python
@router.post("/appointments")
async def create_appointment(
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    # user.sub = Keycloak user ID
    # user.realm_access.roles = ["STUDENT"]
```

### 3. Availability Engine

**Features:**
- Recurring slot definitions (weekly basis)
- iCalendar RRULE support for complex recurrence
- Blackout date handling (professor unavailability)
- Slot expansion: generates all instances over date range
- Booking capacity management (1=individual, N=group)

**Example Flow:**
```
1. Professor creates slot: "Monday 10:00-11:00, max 2 students, every week"
   → Stored as: day_of_week=0, time=10:00-11:00, max_students=2, rrule={FREQ:WEEKLY,BYDAY:MO}

2. Student queries: "Available slots April 25-30"
   → Service expands slots:
      April 28 (Monday) 10:00-11:00 → available_seats=2
      April 28 (Monday) 10:00-11:00 → available_seats=1 (after 1 booking)

3. Blackout applied: "April 25-27 (conference)"
   → Those dates' slots removed from results
```

### 4. Appointment Booking System

**States & Flows:**
```
PENDING (student requested)
  ├─→ APPROVED (professor approved) → COMPLETED (attended) or CANCELLED
  └─→ REJECTED (professor declined)

Redis Pessimistic Locking:
  - Student submits booking
  - SET NX (slot_lock:{slot_id}) with 30s TTL
  - If succeeds: double-booking check passes
  - If fails: slot is being booked by another student → return error
  - After booking: DELETE lock
```

**Late Cancellation Strike:**
- Cancellation < 24 hours before: 1 point strike
- No-show (approved but didn't attend): 2 point strikes
- Expires after 30 days
- 3+ strikes = student blocked from booking

### 5. REST API Endpoints

**Appointments (`/v1/appointments/`):**
```
POST   /                 Create appointment request (student)
GET    /my              List my appointments
GET    /{id}            Get details
PATCH  /{id}            Update/approve/reject (professor)
DELETE /{id}            Cancel appointment
POST   /{id}/complete   Mark as completed (professor)
POST   /{id}/no-show    Record no-show & strike (professor/admin)
```

**Availability (`/v1/availability/`):**
```
POST   /slots           Create slot (professor)
GET    /slots/my        List my slots (professor)
GET    /slots/{prof_id} Get professor's slots (public)
PATCH  /slots/{id}      Update slot
DELETE /slots/{id}      Delete slot
GET    /expanded/{prof_id}  Get expanded instances (for booking UI)
GET    /search          Search available slots by professor/type
```

**Users (`/v1/users/`):**
```
GET    /me              Current user profile
GET    /{id}            Get user profile
GET    /profile/student   Current student profile
PATCH  /profile/student   Update student profile
GET    /profile/professor   Current professor profile
PATCH  /profile/professor   Update professor profile
GET    /{id}/profile/professor  Get professor public profile
```

**Notifications (`/v1/notifications/`):**
```
GET    /my              Get my notifications
POST   /{id}/read       Mark as read
DELETE /{id}            Delete notification
POST   /read-all        Mark all as read
```

**Strikes (`/v1/admin/strikes/`):**
```
GET    /student/{id}        Get student's strikes (admin/student)
POST   /student/{id}/remove/{strike_id}  Remove strike (admin)
GET    /active          List all active strikes (admin)
POST   /student/{id}/block  Block student (admin)
POST   /student/{id}/unblock  Unblock student (admin)
```

### 6. Celery Background Tasks

**Email Notifications** (`send_email_notification`)
- Sends email via Postfix SMTP
- Triggered on appointment state changes
- Development mode: logs instead of sending

**No-Show Detection** (`detect_no_shows`)
- Hourly: finds approved appointments with passed end time
- Issues 2-point strike to student
- Creates IN_APP notification

**Waitlist Processing** (`process_waitlist`)
- When slot becomes available (cancellation/rejection)
- Notify next student on queue with 24h acceptance window
- Auto-offer expires → move to next

**Appointment Reminders** (`send_appointment_reminders`)
- Daily: finds appointments scheduled for next day
- Sends IN_APP notification to both student & professor
- 24 hours before scheduled time

**Strike Expiration** (`expire_strikes`)
- Daily/weekly: finds strikes past expiration date
- Auto-removes them (decrements student strike count)
- Can be overridden by admin removal

### 7. Validation & Error Handling

**Pydantic Schemas** enforce:
- Time format validation: `HH:MM` pattern
- Date format validation: `YYYY-MM-DD` pattern
- Email format validation (EmailStr)
- Max length constraints on text fields
- Enum validation for status/type/topic

**Business Logic Validation:**
- Double-booking prevention (student can't overlap)
- Strike count blocking (3+ strikes → blocked)
- Permission checks (student can only modify own, professor can only approve own)
- Role-based access (admin-only routes)

**Example Error Response:**
```json
{
  "detail": "Student has 3 strikes. Cannot book.",
  "error_code": "STUDENT_BLOCKED",
  "timestamp": "2026-04-22T10:30:00"
}
```

## Key Implementation Details

### Recurrence Expansion

The `AvailabilityService.expand_slot_for_date_range()` method:

```python
# Input: Slot with day_of_week=0 (Monday), 10:00-11:00
# Generates all Mondays in range (April 28, May 5, May 12, ...)

for current_date in [start_date, end_date]:
    if current_date.weekday() == slot.day_of_week:
        if not is_blackedout(current_date):
            booked_count = count_bookings(slot.id, current_date)
            expanded_slots.append(ExpandedSlot(
                date=current_date,
                available_seats=max_students - booked_count
            ))
```

### Pessimistic Locking

Redis ensures no double-booking:

```python
# Student tries to book at 10:00:00.000
lock_token = await redis.set(
    f"slot_lock:{slot_id}",
    {"user_id": student_id, "token": uuid},
    ex=30,      # 30 second TTL
    nx=True     # Only if key doesn't exist
)

if lock_token:
    # Exclusive access for 30s
    # Insert appointment to DB
    # DELETE lock
else:
    # Another student booking same slot
    # Return "Slot no longer available"
```

### Keycloak Integration

JWT validation (simplified for development):

```python
@router.get("/protected")
async def protected_endpoint(
    user: KeycloakUserInfo = Depends(get_current_user)
):
    # user.sub = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    # user.email = "student@fakultet.bg.ac.rs"
    # user.realm_access.roles = ["STUDENT"]
    return {"user_id": user.sub}
```

In production, JWT signature verified against Keycloak's public key.

## Testing Checklist

- [ ] Create a professor and set availability (Monday 10-11, Friday 14-15)
- [ ] Create student and search available slots
- [ ] Student books appointment → status PENDING
- [ ] Professor approves → status APPROVED
- [ ] Verify appointment appears in both user's /my list
- [ ] Student cancels with < 24h left → strikes issued
- [ ] Confirm strike visible in `/v1/admin/strikes/student/{id}`
- [ ] Test double-booking prevention (same student, overlapping time)
- [ ] Test appointment expansion (recurring slots over 30-day range)
- [ ] Test blackout dates (professor blocks April 25-26)
- [ ] Test Celery task: detect_no_shows (mark past appointment as no-show)

## Database Initialization

```bash
# Inside Docker container
python -m alembic upgrade head

# Or manually via psql:
psql -h postgres -U studentska_user -d studentska_db < infra/postgres/init.sql
```

## Running the API

```bash
# Development (with auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production (Docker)
docker-compose up -d backend

# Check health
curl http://localhost:8000/health
# {"status": "ok", "environment": "development"}

# Explore API
# http://localhost:8000/docs  (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

## Next Steps (Phase 2)

1. **Communication System**
   - WebSocket support for real-time chat in appointments
   - File upload to MinIO for documents
   - Ticket management system

2. **Admin Features**
   - Bulk user import (CSV of students)
   - User role assignment
   - System-wide configuration
   - Reporting & analytics

3. **Enhanced Notifications**
   - Email integration (currently Postfix stub)
   - SMS optional
   - Push notifications (Phase 3)

## Files Modified/Created

**New Files (15):**
- `app/models/models.py` — All 14 ORM models
- `app/schemas.py` — All Pydantic schemas
- `app/services/auth.py` — Keycloak integration
- `app/services/availability.py` — Slot expansion logic
- `app/services/appointment.py` — Booking & strikes
- `app/services/redis_service.py` — Pessimistic locking
- `app/services/notification.py` — Notification management
- `app/routes/appointments.py` — Appointment endpoints
- `app/routes/availability.py` — Availability endpoints
- `app/routes/users.py` — User profile endpoints
- `app/routes/notifications.py` — Notification endpoints
- `app/routes/strikes.py` — Strike management endpoints
- `app/tasks/tasks.py` — Celery background jobs
- `backend/requirements.txt` — Updated with `python-dateutil`

**Modified Files (3):**
- `app/main.py` — Added route registration
- `app/services/__init__.py` — Exported services
- `app/routes/__init__.py` — Exported routes

## Configuration

All environment variables in `.env.example`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://studentska_user:password@postgres:5432/studentska_db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Keycloak
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=fakultet
KEYCLOAK_CLIENT_ID=fakultet-backend
KEYCLOAK_CLIENT_SECRET=...

# API
API_TITLE=Studentska Platforma API
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
LOG_LEVEL=INFO
ENVIRONMENT=development

# Features (Phase 1 defaults)
SKIP_JWT_VALIDATION=true  # For development
FEATURE_EMAIL=true
FEATURE_PUSH_NOTIFICATIONS=false  # Deferred to Phase 3
```

---

**Phase 1 is now ready for integration testing. Proceed to Phase 2 when ready.**
