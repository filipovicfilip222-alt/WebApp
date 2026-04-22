"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

# Re-export enums from models
from app.models.models import (
    UserRole,
    AppointmentStatus,
    AppointmentType,
    AppointmentTopic,
    StaffType,
    StrikeReason,
    NotificationType,
    AuditAction,
)


# ============ Auth Schemas ============

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int


class KeycloakUserInfo(BaseModel):
    """User info from Keycloak token."""
    sub: str  # user_id (keycloak_id)
    email: str
    given_name: str | None = None
    family_name: str | None = None
    preferred_username: str | None = None
    realm_access: dict | None = None  # {"roles": ["STUDENT", ...]}


# ============ User Schemas ============

class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    user_role: UserRole
    keycloak_id: str | None = None


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    id: UUID
    user_role: UserRole
    keycloak_id: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """Extended user info with profile details."""
    student_profile: Optional["StudentProfileResponse"] = None
    professor_profile: Optional["ProfessorProfileResponse"] = None


# ============ Student Profile Schemas ============

class StudentProfileBase(BaseModel):
    student_index: str | None = None
    study_program: str | None = None
    year_enrolled: int | None = None


class StudentProfileUpdate(StudentProfileBase):
    pass


class StudentProfileResponse(StudentProfileBase):
    user_id: UUID
    strike_count: int
    is_blocked: bool
    blocked_until: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Professor Profile Schemas ============

class ProfessorProfileBase(BaseModel):
    office_number: str | None = None
    title: str | None = None
    department: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    research_areas: List[str] = []
    publications_link: str | None = None


class ProfessorProfileUpdate(ProfessorProfileBase):
    pass


class ProfessorProfileResponse(ProfessorProfileBase):
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Subject Schemas ============

class SubjectBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class SubjectResponse(SubjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Subject Staff Schemas ============

class SubjectStaffCreate(BaseModel):
    subject_id: UUID
    professor_id: UUID
    staff_type: StaffType


class SubjectStaffResponse(BaseModel):
    id: UUID
    subject_id: UUID
    professor_id: UUID
    staff_type: StaffType
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Availability Slot Schemas ============

class AvailabilitySlotBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")  # "10:00"
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")    # "11:00"
    max_students: int = Field(1, ge=1)
    type: AppointmentType
    recurrence_rule: dict | None = None  # iCalendar RRULE


class AvailabilitySlotCreate(AvailabilitySlotBase):
    pass


class AvailabilitySlotUpdate(BaseModel):
    max_students: int | None = None
    type: AppointmentType | None = None
    recurrence_rule: dict | None = None
    is_active: bool | None = None


class AvailabilitySlotResponse(AvailabilitySlotBase):
    id: UUID
    professor_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpandedSlot(BaseModel):
    """Expanded availability instance on a specific date."""
    slot_id: UUID
    professor_id: UUID
    date: str  # "2026-04-25"
    start_time: str  # "10:00"
    end_time: str    # "11:00"
    type: AppointmentType
    max_students: int
    available_seats: int
    is_blackedout: bool = False


# ============ Blackout Date Schemas ============

class BlackoutDateCreate(BaseModel):
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    reason: str | None = None


class BlackoutDateResponse(BlackoutDateCreate):
    id: UUID
    professor_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Appointment Schemas ============

class AppointmentCreate(BaseModel):
    slot_id: UUID | None = None  # None for manual booking
    student_id: UUID | None = None  # None if student creating own appointment
    professor_id: UUID
    subject_id: UUID | None = None
    type: AppointmentType
    topic: AppointmentTopic
    description: str = Field(..., min_length=1, max_length=1000)
    scheduled_at: datetime
    scheduled_end: datetime


class AppointmentUpdateStudent(BaseModel):
    description: str | None = None
    topic: AppointmentTopic | None = None
    type: AppointmentType | None = None
    scheduled_at: datetime | None = None
    scheduled_end: datetime | None = None


class AppointmentUpdateProfessor(BaseModel):
    status: AppointmentStatus | None = None
    rejection_reason: str | None = None
    cancel_reason: str | None = None


class AppointmentResponse(BaseModel):
    id: UUID
    slot_id: UUID | None
    student_id: UUID
    professor_id: UUID
    subject_id: UUID | None
    status: AppointmentStatus
    type: AppointmentType
    topic: AppointmentTopic
    description: str
    request_date: datetime
    scheduled_at: datetime
    scheduled_end: datetime
    completed_at: datetime | None
    cancel_reason: str | None
    rejection_reason: str | None
    strike_issued: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AppointmentDetailResponse(AppointmentResponse):
    """Extended appointment with related data."""
    student: Optional[UserResponse] = None
    professor: Optional[UserResponse] = None
    subject: Optional[SubjectResponse] = None
    chat_messages: List["TicketChatMessageResponse"] = []


# ============ Appointment Participant Schemas ============

class AppointmentParticipantCreate(BaseModel):
    appointment_id: UUID
    student_id: UUID
    is_group_lead: bool = False


class AppointmentParticipantResponse(BaseModel):
    id: UUID
    appointment_id: UUID
    student_id: UUID
    is_group_lead: bool
    confirmed_at: datetime | None
    participated: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Ticket Chat Schemas ============

class TicketChatMessageCreate(BaseModel):
    appointment_id: UUID
    message: str = Field(..., min_length=1, max_length=5000)


class TicketChatMessageUpdate(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)


class TicketChatMessageResponse(BaseModel):
    id: UUID
    appointment_id: UUID
    user_id: UUID
    message: str
    sent_at: datetime
    read_at: datetime | None
    edited_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class AppointmentFileResponse(BaseModel):
    id: UUID
    appointment_id: UUID
    minio_path: str
    file_name: str
    file_size: int | None
    uploaded_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class AppointmentFileDownloadResponse(BaseModel):
    file_id: UUID
    file_name: str
    download_url: str
    expires_in_seconds: int


# ============ Waitlist Schemas ============

class WaitlistCreate(BaseModel):
    slot_id: UUID


class WaitlistResponse(BaseModel):
    id: UUID
    slot_id: UUID | None
    student_id: UUID
    position: int | None
    requested_at: datetime
    offered_at: datetime | None
    offer_expires_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ CRM Note Schemas ============

class CRMNoteCreate(BaseModel):
    student_id: UUID
    note_text: str = Field(..., min_length=1, max_length=5000)


class CRMNoteUpdate(BaseModel):
    note_text: str = Field(..., min_length=1, max_length=5000)


class CRMNoteResponse(BaseModel):
    id: UUID
    professor_id: UUID
    student_id: UUID
    note_text: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Strike Record Schemas ============

class StrikeRecordCreate(BaseModel):
    student_id: UUID
    appointment_id: UUID | None = None
    reason: StrikeReason
    points: int = 1


class StrikeRecordResponse(BaseModel):
    id: UUID
    student_id: UUID
    appointment_id: UUID | None
    reason: StrikeReason
    points: int
    issued_at: datetime
    expires_at: datetime | None
    removed_reason: str | None
    removed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Notification Schemas ============

class NotificationCreate(BaseModel):
    user_id: UUID
    notification_type: NotificationType
    title: str = Field(..., max_length=255)
    message: str
    related_id: UUID | None = None


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    notification_type: NotificationType
    title: str
    message: str
    related_id: UUID | None
    read_at: datetime | None
    sent_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ FAQ Item Schemas ============

class FAQItemCreate(BaseModel):
    subject_id: UUID | None = None
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    order_index: int = 0


class FAQItemUpdate(BaseModel):
    question: str | None = None
    answer: str | None = None
    order_index: int | None = None


class FAQItemResponse(BaseModel):
    id: UUID
    professor_id: UUID
    subject_id: UUID | None
    question: str
    answer: str
    order_index: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Error Response Schemas ============

class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationErrorDetail(BaseModel):
    loc: tuple
    msg: str
    type: str


class ValidationError(ErrorResponse):
    errors: List[ValidationErrorDetail] = []


# Update forward references
UserDetailResponse.model_rebuild()
AppointmentDetailResponse.model_rebuild()
