"""
Celery tasks for background job processing.
Email notifications, strike detection, waitlist processing, etc.
"""

import logging
from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.tasks.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.models.models import (
    Notification,
    NotificationType,
    Appointment,
    AppointmentStatus,
    User,
)
from app.services.appointment import AppointmentService
from app.config import settings

logger = logging.getLogger(__name__)


def get_async_db():
    """Create async database session for tasks."""
    return AsyncSessionLocal()


@celery_app.task(name="send_email_notification")
def send_email_notification(
    user_id: str,
    title: str,
    message: str,
    recipient_email: str = None,
):
    """
    Send email notification to user.
    
    Args:
        user_id: UUID string
        title: Email subject
        message: Email body
        recipient_email: Override recipient email
    """
    import asyncio

    logger.info(f"Sending email notification to {recipient_email or user_id}")

    try:
        # In development, just log it
        if settings.environment == "development":
            logger.info(f"[DEV] Email: {recipient_email}\nSubject: {title}\n{message}")
            return True

        # In production, send via SMTP
        # This would use smtplib or similar
        logger.info(f"[PROD] Sending email to {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise


@celery_app.task(name="detect_no_shows")
def detect_no_shows():
    """
    Detect no-shows for appointments that have passed.
    
    Called periodically (e.g., every hour).
    Issues strikes to students who didn't show up.
    """
    import asyncio
    from datetime import datetime

    logger.info("Starting no-show detection task")

    async def _run():
        session = get_async_db()
        try:
            from sqlalchemy import select, and_

            # Find approved appointments that have passed
            now = datetime.utcnow()

            stmt = select(Appointment).where(
                and_(
                    Appointment.status == AppointmentStatus.APPROVED,
                    Appointment.scheduled_end < now,
                    Appointment.strike_issued == False,
                )
            )

            result = await session.execute(stmt)
            past_apts = result.scalars().all()

            logger.info(f"Found {len(past_apts)} past approved appointments")

            for apt in past_apts:
                strike = await AppointmentService.detect_no_show(session, apt.id)
                if strike:
                    # Create notification
                    notification = Notification(
                        user_id=apt.student_id,
                        notification_type=NotificationType.IN_APP,
                        title="Disciplinski postupak - Bez odziva",
                        message="Niste se pojavili na zakazanoj konsultaciji. Dobijena ste disciplinska kazna.",
                        related_id=apt.id,
                    )
                    session.add(notification)

            await session.commit()
            logger.info("No-show detection completed")

        except Exception as e:
            logger.error(f"Error in no-show detection: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

    asyncio.run(_run())


@celery_app.task(name="process_waitlist")
def process_waitlist():
    """
    Process waitlist for cancelled/rejected appointments.
    
    When a slot becomes available, notify next student on waitlist.
    """
    logger.info("Starting waitlist processing task")

    # This would:
    # 1. Find cancelled/rejected appointments
    # 2. Get next student from waitlist
    # 3. Offer them the slot with time-limited acceptance

    logger.info("Waitlist processing completed")


@celery_app.task(name="send_appointment_reminders")
def send_appointment_reminders():
    """
    Send appointment reminders 24 hours before.
    
    Called daily.
    """
    import asyncio
    from datetime import timedelta

    logger.info("Starting appointment reminder task")

    async def _run():
        session = get_async_db()
        try:
            from sqlalchemy import select, and_

            # Find appointments scheduled for tomorrow
            now = datetime.utcnow()
            tomorrow_start = now + timedelta(days=1)
            tomorrow_end = now + timedelta(days=2)

            stmt = select(Appointment).where(
                and_(
                    Appointment.status == AppointmentStatus.APPROVED,
                    Appointment.scheduled_at >= tomorrow_start,
                    Appointment.scheduled_at < tomorrow_end,
                )
            )

            result = await session.execute(stmt)
            apts = result.scalars().all()

            logger.info(f"Found {len(apts)} appointments for tomorrow")

            for apt in apts:
                # Get student and professor
                student = await session.get(User, apt.student_id)
                professor = await session.get(User, apt.professor_id)

                # Create notifications
                if student:
                    student_notif = Notification(
                        user_id=apt.student_id,
                        notification_type=NotificationType.IN_APP,
                        title="Podsetnik: Konsultacija sutra",
                        message=f"Vaša konsultacija sa {professor.first_name} {professor.last_name} je zakazana za sutra u {apt.scheduled_at.strftime('%H:%M')}",
                        related_id=apt.id,
                    )
                    session.add(student_notif)

                if professor:
                    prof_notif = Notification(
                        user_id=apt.professor_id,
                        notification_type=NotificationType.IN_APP,
                        title="Podsetnik: Konsultacija sutra",
                        message=f"Imaćete konsultaciju sa {student.first_name} {student.last_name} sutra u {apt.scheduled_at.strftime('%H:%M')}",
                        related_id=apt.id,
                    )
                    session.add(prof_notif)

            await session.commit()
            logger.info(f"Sent {len(apts) * 2} reminder notifications")

        except Exception as e:
            logger.error(f"Error in appointment reminders: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

    asyncio.run(_run())


@celery_app.task(name="expire_strikes")
def expire_strikes():
    """
    Remove expired strikes from students.
    
    Strikes expire after STRIKE_EXPIRY_DAYS (default 30).
    """
    import asyncio

    logger.info("Starting strike expiration task")

    async def _run():
        session = get_async_db()
        try:
            from sqlalchemy import select, and_

            now = datetime.utcnow()

            # Find expired strikes that haven't been removed yet
            stmt = select(StrikeRecord).where(
                and_(
                    StrikeRecord.expires_at <= now,
                    StrikeRecord.removed_at == None,
                )
            )

            result = await session.execute(stmt)
            expired = result.scalars().all()

            logger.info(f"Found {len(expired)} expired strikes")

            # For now, just mark them
            for strike in expired:
                strike.removed_at = now
                strike.removed_reason = "Auto-expired"

                # Update student strike count
                stmt = select(StudentProfile).where(
                    StudentProfile.user_id == strike.student_id
                )
                result = await session.execute(stmt)
                student = result.scalar()

                if student:
                    student.strike_count = max(0, student.strike_count - strike.points)

            await session.commit()
            logger.info(f"Expired {len(expired)} strikes")

        except Exception as e:
            logger.error(f"Error expiring strikes: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

    asyncio.run(_run())


# Import after defining to avoid circular imports
from app.models.models import StudentProfile, StrikeRecord
