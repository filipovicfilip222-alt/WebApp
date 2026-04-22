-- PostgreSQL initialization script
-- Extensions, enums, and initial schema

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Create enums
CREATE TYPE user_role AS ENUM ('STUDENT', 'ASISTENT', 'PROFESOR', 'ADMIN');
CREATE TYPE appointment_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'COMPLETED', 'CANCELLED');
CREATE TYPE appointment_type AS ENUM ('UZIVO', 'ONLINE');
CREATE TYPE appointment_topic AS ENUM ('SEMINAR', 'THEORY', 'EXAM_PREP', 'PROJECT', 'OTHER');
CREATE TYPE staff_type AS ENUM ('PROFESSOR', 'ASISTENT');
CREATE TYPE strike_reason AS ENUM ('LATE_CANCELLATION', 'NO_SHOW');
CREATE TYPE notification_type AS ENUM ('EMAIL', 'IN_APP', 'PUSH');
CREATE TYPE audit_action AS ENUM ('LOGIN_AS', 'BROADCAST', 'BULK_IMPORT', 'STRIKE_REMOVED');

-- Create keycloak database if not exists
CREATE DATABASE keycloak OWNER postgres;

-- Switch to studentska_platforma database for tables
\c studentska_platforma

-- USERS tabela
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    user_role user_role NOT NULL,
    keycloak_id VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- STUDENT_PROFILES tabela
CREATE TABLE student_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    student_index VARCHAR(50) UNIQUE,
    study_program VARCHAR(100),
    year_enrolled SMALLINT,
    strike_count SMALLINT DEFAULT 0,
    is_blocked BOOLEAN DEFAULT FALSE,
    blocked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PROFESSOR_PROFILES tabela
CREATE TABLE professor_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    office_number VARCHAR(50),
    title VARCHAR(100),
    department VARCHAR(150),
    avatar_url VARCHAR(500),
    bio TEXT,
    research_areas TEXT[] DEFAULT '{}',
    publications_link VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SUBJECTS tabela
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SUBJECT_STAFF tabela
CREATE TABLE subject_staff (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    professor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    staff_type staff_type NOT NULL,
    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subject_id, professor_id, staff_type)
);

-- AVAILABILITY_SLOTS tabela
CREATE TABLE availability_slots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    professor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    max_students SMALLINT DEFAULT 1,
    type appointment_type NOT NULL,
    recurrence_rule JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (end_time > start_time)
);

-- BLACKOUT_DATES tabela
CREATE TABLE blackout_dates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    professor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (end_date >= start_date)
);

-- APPOINTMENTS tabela
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slot_id UUID REFERENCES availability_slots(id) ON DELETE SET NULL,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    professor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
    status appointment_status DEFAULT 'PENDING',
    type appointment_type NOT NULL,
    topic appointment_topic NOT NULL,
    description TEXT NOT NULL,
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scheduled_at TIMESTAMP NOT NULL,
    scheduled_end TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    cancel_reason TEXT,
    strike_issued BOOLEAN DEFAULT FALSE,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (scheduled_end > scheduled_at)
);

-- APPOINTMENT_PARTICIPANTS tabela
CREATE TABLE appointment_participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_group_lead BOOLEAN DEFAULT FALSE,
    confirmed_at TIMESTAMP,
    participated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(appointment_id, student_id)
);

-- APPOINTMENT_FILES tabela
CREATE TABLE appointment_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    minio_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TICKET_CHAT_MESSAGES tabela
CREATE TABLE ticket_chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    edited_at TIMESTAMP
);

-- WAITLIST tabela
CREATE TABLE waitlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slot_id UUID REFERENCES availability_slots(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    position SMALLINT,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    offered_at TIMESTAMP,
    offer_expires_at TIMESTAMP,
    UNIQUE(slot_id, student_id)
);

-- CRM_NOTES tabela
CREATE TABLE crm_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    professor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- STRIKE_RECORDS tabela
CREATE TABLE strike_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    appointment_id UUID REFERENCES appointments(id) ON DELETE SET NULL,
    reason strike_reason NOT NULL,
    points SMALLINT NOT NULL DEFAULT 1,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    removed_reason TEXT,
    removed_at TIMESTAMP,
    removed_by UUID REFERENCES users(id)
);

-- FAQ_ITEMS tabela
CREATE TABLE faq_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    professor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    order_index SMALLINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CANNED_RESPONSES tabela
CREATE TABLE canned_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    professor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    message_text TEXT NOT NULL,
    response_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NOTIFICATIONS tabela
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type notification_type NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    related_id UUID,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP
);

-- AUDIT_LOG tabela
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action audit_action NOT NULL,
    target_user_id UUID REFERENCES users(id),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indeksi za performanse
CREATE INDEX idx_users_keycloak_id ON users(keycloak_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_user_role ON users(user_role);

CREATE INDEX idx_appointments_student_id ON appointments(student_id);
CREATE INDEX idx_appointments_professor_id ON appointments(professor_id);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_appointments_scheduled_at ON appointments(scheduled_at);

CREATE INDEX idx_availability_slots_professor_id ON availability_slots(professor_id);
CREATE INDEX idx_availability_slots_is_active ON availability_slots(is_active);

CREATE INDEX idx_waitlist_student_id ON waitlist(student_id);
CREATE INDEX idx_waitlist_requested_at ON waitlist(requested_at);

CREATE INDEX idx_strike_records_student_id ON strike_records(student_id);
CREATE INDEX idx_strike_records_expires_at ON strike_records(expires_at);

CREATE INDEX idx_crm_notes_professor_student ON crm_notes(professor_id, student_id);

CREATE INDEX idx_ticket_chat_appointment_id ON ticket_chat_messages(appointment_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_audit_log_admin_id ON audit_log(admin_id);

-- Grant permissions to application user
-- (Later created by application setup script)
