"""
API endpoints for appointments and consultation booking.
"""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services import (
    get_current_user,
    AppointmentService,
    AvailabilityService,
)
from app.schemas import (
    KeycloakUserInfo,
    AppointmentResponse,
    AppointmentCreate,
    AppointmentUpdateStudent,
    AppointmentUpdateProfessor,
    AppointmentDetailResponse,
)
from app.models.models import AppointmentStatus

router = APIRouter(
    prefix="/v1/appointments",
    tags=["appointments"],
)


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_appointment(
    appointment_data: AppointmentCreate,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Create a new appointment request.
    
    Student creates a consultation request with a professor.
    Appointment starts in PENDING status and waits for professor approval.
    """
    # Student can only create appointments for themselves
    appointment = await AppointmentService.create_appointment(
        session=session,
        student_id=UUID(user.sub),
        professor_id=appointment_data.professor_id,
        appointment_data=appointment_data,
    )

    await session.commit()
    return appointment


@router.get(
    "/my",
    response_model=list[AppointmentResponse],
)
async def get_my_appointments(
    status_filter: AppointmentStatus | None = Query(None),
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Get current user's appointments.
    
    Returns student's own appointments or professor's consultation appointments.
    """
    user_id = UUID(user.sub)

    # Get both as student and professor
    student_apts = await AppointmentService.get_student_appointments(
        session, user_id, status_filter
    )
    professor_apts = await AppointmentService.get_professor_appointments(
        session, user_id, status_filter
    )

    # Combine and sort by scheduled_at
    all_apts = student_apts + professor_apts
    all_apts.sort(key=lambda x: x.scheduled_at)

    return all_apts


@router.get(
    "/{appointment_id}",
    response_model=AppointmentDetailResponse,
)
async def get_appointment(
    appointment_id: UUID,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get appointment details."""
    from app.models.models import Appointment

    appointment = await session.get(Appointment, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    # Check permissions: student, professor, or admin
    user_id = UUID(user.sub)
    is_involved = (
        appointment.student_id == user_id
        or appointment.professor_id == user_id
    )

    user_roles = (user.realm_access or {}).get("roles", [])
    if not is_involved and "ADMIN" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this appointment",
        )

    return appointment


@router.patch(
    "/{appointment_id}",
    response_model=AppointmentResponse,
)
async def update_appointment(
    appointment_id: UUID,
    update_data: AppointmentUpdateStudent | AppointmentUpdateProfessor,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Update appointment.
    
    Students can modify description/time of PENDING appointments.
    Professors can approve/reject/cancel appointments.
    """
    from app.models.models import Appointment

    appointment = await session.get(Appointment, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    user_id = UUID(user.sub)

    # Handle professor actions (approve/reject)
    if isinstance(update_data, AppointmentUpdateProfessor):
        if appointment.professor_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only professor can approve/reject",
            )

        if update_data.status == AppointmentStatus.APPROVED:
            appointment = await AppointmentService.approve_appointment(
                session, appointment_id
            )
        elif update_data.status == AppointmentStatus.REJECTED:
            if not update_data.rejection_reason:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rejection reason required",
                )
            appointment = await AppointmentService.reject_appointment(
                session,
                appointment_id,
                update_data.rejection_reason,
            )

    # Handle student actions (modify description, reschedule)
    elif isinstance(update_data, AppointmentUpdateStudent):
        if appointment.student_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only student can modify appointment",
            )

        if appointment.status != AppointmentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only modify PENDING appointments",
            )

        if update_data.description:
            appointment.description = update_data.description
        if update_data.topic:
            appointment.topic = update_data.topic
        if update_data.type:
            appointment.type = update_data.type
        if update_data.scheduled_at and update_data.scheduled_end:
            appointment.scheduled_at = update_data.scheduled_at
            appointment.scheduled_end = update_data.scheduled_end

    await session.commit()
    return appointment


@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_appointment(
    appointment_id: UUID,
    cancel_reason: str = Query(..., min_length=1),
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Cancel an appointment.
    
    Issues late cancellation strike if cancelled < 24 hours before.
    """
    user_id = UUID(user.sub)

    appointment, strike = await AppointmentService.cancel_appointment(
        session,
        appointment_id,
        cancel_reason,
        user_id,
    )

    await session.commit()


@router.post(
    "/{appointment_id}/complete",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def complete_appointment(
    appointment_id: UUID,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Mark appointment as completed.
    
    Only professor can mark as complete.
    """
    from app.models.models import Appointment

    appointment = await session.get(Appointment, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    user_id = UUID(user.sub)

    if appointment.professor_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professor can mark as complete",
        )

    await AppointmentService.mark_appointment_completed(session, appointment_id)
    await session.commit()


@router.post(
    "/{appointment_id}/no-show",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def detect_no_show(
    appointment_id: UUID,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Detect and record no-show for appointment.
    
    Issues 2-point strike to student.
    Only professor or admin can call this.
    """
    from app.models.models import Appointment

    appointment = await session.get(Appointment, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    user_id = UUID(user.sub)

    # Check permissions
    is_professor = appointment.professor_id == user_id
    is_admin = "ADMIN" in (
        getattr(user, "realm_access", {}).get("roles", [])
    )

    if not (is_professor or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professor or admin can record no-show",
        )

    strike = await AppointmentService.detect_no_show(session, appointment_id)
    await session.commit()
