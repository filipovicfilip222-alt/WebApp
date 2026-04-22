"""
SQLAlchemy ORM models for Studentska Platforma.
All models inherit from BaseModel which provides id, created_at, updated_at.
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, ARRAY, JSON, UUID, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from uuid import UUID as PyUUID
import enum

from app.db.base import Base, BaseModel


# Enums
class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    ASISTENT = "ASISTENT"
    PROFESOR = "PROFESOR"
    ADMIN = "ADMIN"


class AppointmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AppointmentType(str, enum.Enum):
    UZIVO = "UZIVO"
    ONLINE = "ONLINE"


class AppointmentTopic(str, enum.Enum):
    SEMINAR = "SEMINAR"
    THEORY = "THEORY"
    EXAM_PREP = "EXAM_PREP"
    PROJECT = "PROJECT"
    OTHER = "OTHER"


class StaffType(str, enum.Enum):
    PROFESSOR = "PROFESSOR"
    ASISTENT = "ASISTENT"


class StrikeReason(str, enum.Enum):
    LATE_CANCELLATION = "LATE_CANCELLATION"
    NO_SHOW = "NO_SHOW"


class NotificationType(str, enum.Enum):
    EMAIL = "EMAIL"
    IN_APP = "IN_APP"
    PUSH = "PUSH"


class AuditAction(str, enum.Enum):
    LOGIN_AS = "LOGIN_AS"
    BROADCAST = "BROADCAST"
    BULK_IMPORT = "BULK_IMPORT"
    STRIKE_REMOVED = "STRIKE_REMOVED"


# Models
class User(Base, BaseModel):
    """User model with role-based access control."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    user_role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), index=True)
    keycloak_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    professor_profile = relationship("ProfessorProfile", back_populates="user", uselist=False)
    appointments_as_student = relationship(
        "Appointment", foreign_keys="Appointment.student_id", back_populates="student"
    )
    appointments_as_professor = relationship(
        "Appointment", foreign_keys="Appointment.professor_id", back_populates="professor"
    )
    crm_notes = relationship("CRMNote", back_populates="professor")
    strike_records = relationship("StrikeRecord", back_populates="student")
    notifications = relationship("Notification", back_populates="user")

    def __repr__(self):
        return f"<User {self.email} ({self.user_role})>"


class StudentProfile(Base, BaseModel):
    """Extended profile for STUDENT role."""
    __tablename__ = "student_profiles"

    user_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    student_index: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    study_program: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year_enrolled: Mapped[int | None] = mapped_column(Integer, nullable=True)
    strike_count: Mapped[int] = mapped_column(Integer, default=0)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="student_profile", lazy="joined")

    def __repr__(self):
        return f"<StudentProfile {self.user.email}>"


class ProfessorProfile(Base, BaseModel):
    """Extended profile for PROFESOR/ASISTENT role."""
    __tablename__ = "professor_profiles"

    user_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    office_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Dr., Prof., Asist.
    department: Mapped[str | None] = mapped_column(String(150), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_areas: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    publications_link: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="professor_profile", lazy="joined")

    def __repr__(self):
        return f"<ProfessorProfile {self.user.email}>"


class Subject(Base, BaseModel):
    """Subject/Course model."""
    __tablename__ = "subjects"

    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    staff = relationship("SubjectStaff", back_populates="subject")
    faq_items = relationship("FAQItem", back_populates="subject")

    def __repr__(self):
        return f"<Subject {self.code} - {self.name}>"


class SubjectStaff(Base, BaseModel):
    """N:M relationship between Subject and Professor/Assistant."""
    __tablename__ = "subject_staff"
    __table_args__ = (
        UniqueConstraint("subject_id", "professor_id", "staff_type"),
    )

    subject_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    professor_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    staff_type: Mapped[StaffType] = mapped_column(SQLEnum(StaffType))

    # Relationships
    subject = relationship("Subject", back_populates="staff")

    def __repr__(self):
        return f"<SubjectStaff {self.staff_type}>"


class AvailabilitySlot(Base, BaseModel):
    """Recurring availability slot for professor."""
    __tablename__ = "availability_slots"
    __table_args__ = (
        CheckConstraint("day_of_week >= 0 AND day_of_week <= 6"),
        CheckConstraint("end_time > start_time"),
    )

    professor_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    day_of_week: Mapped[int] = mapped_column(Integer)  # 0=Monday, 6=Sunday
    start_time: Mapped[str] = mapped_column(String(5))  # "10:00" format
    end_time: Mapped[str] = mapped_column(String(5))    # "11:00" format
    max_students: Mapped[int] = mapped_column(Integer, default=1)  # 1=individual, N=group
    type: Mapped[AppointmentType] = mapped_column(SQLEnum(AppointmentType))
    recurrence_rule: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # iCalendar RRULE
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Relationships
    appointments = relationship("Appointment", back_populates="slot")

    def __repr__(self):
        return f"<AvailabilitySlot {self.day_of_week} {self.start_time}-{self.end_time}>"


class BlackoutDate(Base, BaseModel):
    """Blocked period for professor (sick leave, conference, etc.)."""
    __tablename__ = "blackout_dates"
    __table_args__ = (
        CheckConstraint("end_date >= start_date"),
    )

    professor_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    start_date: Mapped[str] = mapped_column(String(10))  # "2026-04-25" format
    end_date: Mapped[str] = mapped_column(String(10))
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self):
        return f"<BlackoutDate {self.start_date} to {self.end_date}>"


class Appointment(Base, BaseModel):
    """Scheduled appointment/consultation."""
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint("scheduled_end > scheduled_at"),
    )

    slot_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("availability_slots.id"), nullable=True)
    student_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    professor_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    subject_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True)

    status: Mapped[AppointmentStatus] = mapped_column(SQLEnum(AppointmentStatus), default=AppointmentStatus.PENDING, index=True)
    type: Mapped[AppointmentType] = mapped_column(SQLEnum(AppointmentType))
    topic: Mapped[AppointmentTopic] = mapped_column(SQLEnum(AppointmentTopic))
    description: Mapped[str] = mapped_column(Text)

    request_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    strike_issued: Mapped[bool] = mapped_column(Boolean, default=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    slot = relationship("AvailabilitySlot", back_populates="appointments")
    student = relationship("User", foreign_keys=[student_id], back_populates="appointments_as_student")
    professor = relationship("User", foreign_keys=[professor_id], back_populates="appointments_as_professor")
    participants = relationship("AppointmentParticipant", back_populates="appointment")
    files = relationship("AppointmentFile", back_populates="appointment")
    chat_messages = relationship("TicketChatMessage", back_populates="appointment")

    def __repr__(self):
        return f"<Appointment {self.student.email} -> {self.professor.email}>"


class AppointmentParticipant(Base, BaseModel):
    """Participant in a group consultation."""
    __tablename__ = "appointment_participants"
    __table_args__ = (
        UniqueConstraint("appointment_id", "student_id"),
    )

    appointment_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("appointments.id"))
    student_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_group_lead: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    participated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    appointment = relationship("Appointment", back_populates="participants")


class AppointmentFile(Base, BaseModel):
    """File uploaded to an appointment."""
    __tablename__ = "appointment_files"

    appointment_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("appointments.id"))
    minio_path: Mapped[str] = mapped_column(String(500))  # s3://bucket/path/file
    file_name: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)  # In bytes
    uploaded_by: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    appointment = relationship("Appointment", back_populates="files")

    def __repr__(self):
        return f"<AppointmentFile {self.file_name}>"


class TicketChatMessage(Base, BaseModel):
    """In-app ticket chat message."""
    __tablename__ = "ticket_chat_messages"

    appointment_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("appointments.id"), index=True)
    user_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    message: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    appointment = relationship("Appointment", back_populates="chat_messages")

    def __repr__(self):
        return f"<TicketChatMessage {self.user_id}>"


class Waitlist(Base, BaseModel):
    """Student waitlist for appointment slot."""
    __tablename__ = "waitlist"
    __table_args__ = (
        UniqueConstraint("slot_id", "student_id"),
    )

    slot_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("availability_slots.id"), nullable=True)
    student_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    offered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    offer_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Waitlist {self.student_id} position {self.position}>"


class CRMNote(Base, BaseModel):
    """Private CRM note by professor about student."""
    __tablename__ = "crm_notes"

    professor_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    student_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    note_text: Mapped[str] = mapped_column(Text)

    # Relationships
    professor = relationship("User", foreign_keys=[professor_id], back_populates="crm_notes")

    def __repr__(self):
        return f"<CRMNote by {self.professor_id}>"


class StrikeRecord(Base, BaseModel):
    """Strike record for student misconduct."""
    __tablename__ = "strike_records"

    student_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    appointment_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True)
    reason: Mapped[StrikeReason] = mapped_column(SQLEnum(StrikeReason))
    points: Mapped[int] = mapped_column(Integer, default=1)  # 1 or 2
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    removed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    removed_by: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    student = relationship("User", foreign_keys=[student_id], back_populates="strike_records")

    def __repr__(self):
        return f"<StrikeRecord {self.student_id} - {self.reason}>"


class FAQItem(Base, BaseModel):
    """FAQ item on professor's profile."""
    __tablename__ = "faq_items"

    professor_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    subject_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    subject = relationship("Subject", back_populates="faq_items")

    def __repr__(self):
        return f"<FAQItem {self.question[:50]}>"


class CannedResponse(Base, BaseModel):
    """Templated response for rejecting appointments."""
    __tablename__ = "canned_responses"

    professor_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(100))
    message_text: Mapped[str] = mapped_column(Text)
    response_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # REJECTION, DELEGATION, etc.

    def __repr__(self):
        return f"<CannedResponse {self.title}>"


class Notification(Base, BaseModel):
    """User notification (email, in-app, push)."""
    __tablename__ = "notifications"

    user_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    notification_type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    related_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)  # appointment_id, user_id, etc.
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.user_id}>"


class AuditLog(Base, BaseModel):
    """Admin action audit log."""
    __tablename__ = "audit_log"

    admin_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    action: Mapped[AuditAction] = mapped_column(SQLEnum(AuditAction))
    target_user_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.admin_id}>"
