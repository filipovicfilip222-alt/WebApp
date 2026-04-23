"""
Appointment service for booking, modification, and cancellation logic.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from fastapi import HTTPException, status

from app.models.models import (
    Appointment,
    AppointmentStatus,
    AppointmentType,
    AppointmentTopic,
    AvailabilitySlot,
    StudentProfile,
    User,
    Waitlist,
    StrikeRecord,
    StrikeReason,
)
from app.schemas_module import AppointmentCreate, AppointmentUpdateProfessor
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)

# Configuration
STRIKE_EXPIRY_DAYS = 30
NO_SHOW_POINTS = 2
LATE_CANCELLATION_POINTS = 1
LATE_CANCELLATION_HOURS = 24


class AppointmentService:
    """Service for appointment operations."""

    @staticmethod
    async def validate_student_can_book(
        session: AsyncSession,
        student_id: UUID,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that student is not blocked or over strike limit.
        
        Returns:
            (is_valid, error_message)
        """
        stmt = select(StudentProfile).where(StudentProfile.user_id == student_id)
        result = await session.execute(stmt)
        profile = result.scalar()

        if not profile:
            return False, "Student profile not found"

        if profile.is_blocked:
            if profile.blocked_until:
                return False, f"Student is blocked until {profile.blocked_until}"
            else:
                return False, "Student is permanently blocked"

        # Check strike count (typically block at 3+ strikes)
        if profile.strike_count >= 3:
            return False, f"Student has {profile.strike_count} strikes. Cannot book."

        return True, None

    @staticmethod
    async def check_double_booking(
        session: AsyncSession,
        student_id: UUID,
        scheduled_at: datetime,
        scheduled_end: datetime,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if student already has overlapping appointment.
        
        Returns:
            (has_overlap, error_message)
        """
        # Find non-cancelled appointments in same time window
        stmt = select(Appointment).where(
            and_(
                Appointment.student_id == student_id,
                Appointment.status != AppointmentStatus.CANCELLED,
                Appointment.status != AppointmentStatus.REJECTED,
                # Overlap check: other_start < our_end AND other_end > our_start
                Appointment.scheduled_at < scheduled_end,
                Appointment.scheduled_end > scheduled_at,
            )
        )
        result = await session.execute(stmt)
        overlapping = result.scalar()

        if overlapping:
            return True, "Student already has appointment at this time"

        return False, None

    @staticmethod
    async def create_appointment(
        session: AsyncSession,
        student_id: UUID,
        professor_id: UUID,
        appointment_data: AppointmentCreate,
    ) -> Appointment:
        """
        Create a new appointment.
        
        Args:
            session: Database session
            student_id: Requesting student ID
            professor_id: Target professor ID
            appointment_data: Appointment details
            
        Returns:
            Created Appointment object
            
        Raises:
            HTTPException if validation fails
        """
        # Validate student can book
        is_valid, error_msg = await AppointmentService.validate_student_can_book(
            session, student_id
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        # Validate no double booking
        has_overlap, error_msg = await AppointmentService.check_double_booking(
            session,
            student_id,
            appointment_data.scheduled_at,
            appointment_data.scheduled_end,
        )
        if has_overlap:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        # Create appointment (status: PENDING, awaiting professor approval)
        appointment = Appointment(
            student_id=student_id,
            professor_id=professor_id,
            slot_id=appointment_data.slot_id,
            subject_id=appointment_data.subject_id,
            type=appointment_data.type,
            topic=appointment_data.topic,
            description=appointment_data.description,
            scheduled_at=appointment_data.scheduled_at,
            scheduled_end=appointment_data.scheduled_end,
            status=AppointmentStatus.PENDING,
            request_date=datetime.utcnow(),
        )

        session.add(appointment)
        await session.flush()  # Get ID without commit

        logger.info(
            f"Created appointment {appointment.id}: "
            f"{student_id} -> {professor_id} on {appointment_data.scheduled_at}"
        )

        return appointment

    @staticmethod
    async def approve_appointment(
        session: AsyncSession,
        appointment_id: UUID,
    ) -> Appointment:
        """Approve a pending appointment."""
        stmt = select(Appointment).where(Appointment.id == appointment_id)
        result = await session.execute(stmt)
        appointment = result.scalar()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found",
            )

        if appointment.status != AppointmentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Can only approve PENDING appointments, got {appointment.status}",
            )

        appointment.status = AppointmentStatus.APPROVED

        logger.info(f"Approved appointment {appointment_id}")

        return appointment

    @staticmethod
    async def reject_appointment(
        session: AsyncSession,
        appointment_id: UUID,
        rejection_reason: str,
    ) -> Appointment:
        """Reject a pending appointment."""
        stmt = select(Appointment).where(Appointment.id == appointment_id)
        result = await session.execute(stmt)
        appointment = result.scalar()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found",
            )

        if appointment.status != AppointmentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Can only reject PENDING appointments, got {appointment.status}",
            )

        appointment.status = AppointmentStatus.REJECTED
        appointment.rejection_reason = rejection_reason

        logger.info(f"Rejected appointment {appointment_id}: {rejection_reason}")

        return appointment

    @staticmethod
    async def cancel_appointment(
        session: AsyncSession,
        appointment_id: UUID,
        cancel_reason: str,
        requesting_user_id: UUID,
    ) -> Tuple[Appointment, Optional[StrikeRecord]]:
        """
        Cancel an appointment.
        Issues strike if cancelled too close to scheduled time.
        
        Returns:
            (Appointment, StrikeRecord or None)
        """
        stmt = select(Appointment).where(Appointment.id == appointment_id)
        result = await session.execute(stmt)
        appointment = result.scalar()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found",
            )

        if appointment.status == AppointmentStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment already cancelled",
            )

        if appointment.status == AppointmentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel completed appointment",
            )

        # Check if late cancellation (student initiating)
        strike_record = None
        if requesting_user_id == appointment.student_id:
            time_until = appointment.scheduled_at - datetime.utcnow()
            if time_until < timedelta(hours=LATE_CANCELLATION_HOURS):
                # Issue strike
                strike_record = StrikeRecord(
                    student_id=appointment.student_id,
                    appointment_id=appointment_id,
                    reason=StrikeReason.LATE_CANCELLATION,
                    points=LATE_CANCELLATION_POINTS,
                    issued_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=STRIKE_EXPIRY_DAYS),
                )
                session.add(strike_record)
                appointment.strike_issued = True

                # Update student strike count
                student_stmt = select(StudentProfile).where(
                    StudentProfile.user_id == appointment.student_id
                )
                student_result = await session.execute(student_stmt)
                student = student_result.scalar()
                if student:
                    student.strike_count += LATE_CANCELLATION_POINTS

                logger.info(
                    f"Late cancellation strike issued to {appointment.student_id} "
                    f"for appointment {appointment_id}"
                )

        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancel_reason = cancel_reason

        logger.info(f"Cancelled appointment {appointment_id}: {cancel_reason}")

        return appointment, strike_record

    @staticmethod
    async def mark_appointment_completed(
        session: AsyncSession,
        appointment_id: UUID,
    ) -> Appointment:
        """Mark appointment as completed."""
        stmt = select(Appointment).where(Appointment.id == appointment_id)
        result = await session.execute(stmt)
        appointment = result.scalar()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found",
            )

        if appointment.status != AppointmentStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Can only complete APPROVED appointments, got {appointment.status}",
            )

        appointment.status = AppointmentStatus.COMPLETED
        appointment.completed_at = datetime.utcnow()

        logger.info(f"Marked appointment {appointment_id} as completed")

        return appointment

    @staticmethod
    async def detect_no_show(
        session: AsyncSession,
        appointment_id: UUID,
    ) -> Optional[StrikeRecord]:
        """
        Detect no-show for an appointment and issue strike.
        Called after appointment scheduled time has passed.
        
        Returns:
            StrikeRecord if issued, None otherwise
        """
        stmt = select(Appointment).where(Appointment.id == appointment_id)
        result = await session.execute(stmt)
        appointment = result.scalar()

        if not appointment or appointment.status == AppointmentStatus.CANCELLED:
            return None

        if appointment.status == AppointmentStatus.COMPLETED:
            return None

        # No-show: was approved but not completed
        if appointment.status == AppointmentStatus.APPROVED:
            strike_record = StrikeRecord(
                student_id=appointment.student_id,
                appointment_id=appointment_id,
                reason=StrikeReason.NO_SHOW,
                points=NO_SHOW_POINTS,
                issued_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=STRIKE_EXPIRY_DAYS),
            )
            session.add(strike_record)
            appointment.strike_issued = True

            # Update student strike count
            student_stmt = select(StudentProfile).where(
                StudentProfile.user_id == appointment.student_id
            )
            student_result = await session.execute(student_stmt)
            student = student_result.scalar()
            if student:
                student.strike_count += NO_SHOW_POINTS

            logger.info(
                f"No-show strike issued to {appointment.student_id} "
                f"for appointment {appointment_id}"
            )

            return strike_record

        return None

    @staticmethod
    async def get_student_appointments(
        session: AsyncSession,
        student_id: UUID,
        status_filter: Optional[AppointmentStatus] = None,
    ) -> list[Appointment]:
        """Get student's appointments."""
        stmt = select(Appointment).where(Appointment.student_id == student_id)

        if status_filter:
            stmt = stmt.where(Appointment.status == status_filter)

        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_professor_appointments(
        session: AsyncSession,
        professor_id: UUID,
        status_filter: Optional[AppointmentStatus] = None,
    ) -> list[Appointment]:
        """Get professor's appointments."""
        stmt = select(Appointment).where(Appointment.professor_id == professor_id)

        if status_filter:
            stmt = stmt.where(Appointment.status == status_filter)

        result = await session.execute(stmt)
        return result.scalars().all()
