"""
Availability service for managing professor availability slots and recurrence expansion.
"""

from datetime import datetime, timedelta, date
from typing import List, Optional
import logging
from dateutil import rrule
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.models import (
    AvailabilitySlot,
    BlackoutDate,
    Appointment,
    Waitlist,
    User,
)
from app.schemas_module import ExpandedSlot, AvailabilitySlotResponse

logger = logging.getLogger(__name__)


class AvailabilityService:
    """Service for managing professor availability and slot expansion."""

    WEEKDAYS = {
        0: "MO",  # Monday
        1: "TU",
        2: "WE",
        3: "TH",
        4: "FR",
        5: "SA",
        6: "SU",
    }

    @staticmethod
    def parse_time(time_str: str) -> tuple[int, int]:
        """Parse time string 'HH:MM' to (hour, minute) tuple."""
        parts = time_str.split(":")
        return int(parts[0]), int(parts[1])

    @staticmethod
    def time_to_minutes(time_str: str) -> int:
        """Convert 'HH:MM' to total minutes."""
        hour, minute = AvailabilityService.parse_time(time_str)
        return hour * 60 + minute

    @staticmethod
    def minutes_to_time(minutes: int) -> str:
        """Convert total minutes back to 'HH:MM'."""
        hour = minutes // 60
        minute = minutes % 60
        return f"{hour:02d}:{minute:02d}"

    @staticmethod
    def is_date_in_range(
        target_date: date,
        blackout_start: str,  # "2026-04-25"
        blackout_end: str,
    ) -> bool:
        """Check if target_date falls within blackout range (inclusive)."""
        start = datetime.strptime(blackout_start, "%Y-%m-%d").date()
        end = datetime.strptime(blackout_end, "%Y-%m-%d").date()
        return start <= target_date <= end

    @classmethod
    async def expand_slot_for_date_range(
        cls,
        session: AsyncSession,
        professor_id,
        start_date: date,
        end_date: date,
    ) -> List[ExpandedSlot]:
        """
        Expand all active availability slots for a professor over a date range.
        
        This returns all instances of recurring slots, accounting for blackouts.
        """
        expanded = []

        # Fetch all active slots for professor
        stmt = select(AvailabilitySlot).where(
            and_(
                AvailabilitySlot.professor_id == professor_id,
                AvailabilitySlot.is_active == True,
            )
        )
        result = await session.execute(stmt)
        slots = result.scalars().all()

        # Fetch blackout dates
        blackout_stmt = select(BlackoutDate).where(
            BlackoutDate.professor_id == professor_id
        )
        blackout_result = await session.execute(blackout_stmt)
        blackouts = blackout_result.scalars().all()

        # For each slot, generate instances
        for slot in slots:
            # Generate dates with matching day_of_week
            current_date = start_date
            while current_date <= end_date:
                # Check if this date's weekday matches slot's day_of_week
                if current_date.weekday() == slot.day_of_week:
                    # Check if blackedout
                    is_blackedout = any(
                        cls.is_date_in_range(current_date, bd.start_date, bd.end_date)
                        for bd in blackouts
                    )

                    # Get booked count for this slot instance
                    booked_count = await cls._count_booked_appointments(
                        session, slot.id, current_date
                    )
                    available_seats = max(0, slot.max_students - booked_count)

                    expanded_slot = ExpandedSlot(
                        slot_id=slot.id,
                        professor_id=slot.professor_id,
                        date=current_date.isoformat(),
                        start_time=slot.start_time,
                        end_time=slot.end_time,
                        type=slot.type,
                        max_students=slot.max_students,
                        available_seats=available_seats,
                        is_blackedout=is_blackedout,
                    )
                    expanded.append(expanded_slot)

                current_date += timedelta(days=1)

        # Sort by date and time
        expanded.sort(
            key=lambda x: (x.date, x.start_time),
        )

        return expanded

    @staticmethod
    async def _count_booked_appointments(
        session: AsyncSession,
        slot_id,
        target_date: date,
    ) -> int:
        """Count approved/completed appointments for a slot on a specific date."""
        from app.models.models import AppointmentStatus

        # Find appointments on this slot and date that are not cancelled/rejected
        stmt = select(Appointment).where(
            and_(
                Appointment.slot_id == slot_id,
                # Date matches the target date
                Appointment.scheduled_at >= datetime.combine(target_date, datetime.min.time()),
                Appointment.scheduled_at < datetime.combine(target_date + timedelta(days=1), datetime.min.time()),
                # Status is confirmed
                Appointment.status.in_([
                    AppointmentStatus.APPROVED,
                    AppointmentStatus.COMPLETED,
                ]),
            )
        )
        result = await session.execute(stmt)
        appointments = result.scalars().all()
        return len(appointments)

    @staticmethod
    async def get_available_slots(
        session: AsyncSession,
        professor_id,
        start_date: date,
        end_date: date,
        include_full: bool = False,  # If True, return even fully booked slots
    ) -> List[ExpandedSlot]:
        """Get available slots for booking (filtered by availability)."""
        all_expanded = await AvailabilityService.expand_slot_for_date_range(
            session, professor_id, start_date, end_date
        )

        # Filter to only available slots (unless include_full)
        if include_full:
            return [s for s in all_expanded if not s.is_blackedout]
        else:
            return [
                s
                for s in all_expanded
                if s.available_seats > 0 and not s.is_blackedout
            ]

    @staticmethod
    async def create_recurrence_rule(
        day_of_week: int,
        start_date: Optional[str] = None,  # "2026-04-25"
        end_date: Optional[str] = None,
    ) -> dict:
        """
        Generate iCalendar RRULE for recurring availability.
        
        Args:
            day_of_week: 0=Monday, 6=Sunday
            start_date: Start date for recurrence
            end_date: End date for recurrence
            
        Returns:
            Dict with RRULE components
        """
        # Default: recurring weekly forever
        rrule_dict = {
            "FREQ": "WEEKLY",
            "BYDAY": AvailabilityService.WEEKDAYS[day_of_week],
        }

        if start_date:
            rrule_dict["DTSTART"] = start_date

        if end_date:
            rrule_dict["UNTIL"] = end_date

        return rrule_dict

    @staticmethod
    def parse_recurrence_rule(rrule_dict: Optional[dict]) -> Optional[rrule.rrule]:
        """
        Parse RRULE dict to Python dateutil.rrule object.
        
        Returns None if invalid or no rule.
        """
        if not rrule_dict:
            return None

        try:
            freq_map = {
                "DAILY": rrule.DAILY,
                "WEEKLY": rrule.WEEKLY,
                "MONTHLY": rrule.MONTHLY,
                "YEARLY": rrule.YEARLY,
            }

            freq = freq_map.get(rrule_dict.get("FREQ", "WEEKLY"), rrule.WEEKLY)

            # Parse DTSTART if present
            dtstart = None
            if "DTSTART" in rrule_dict:
                dtstart_str = rrule_dict["DTSTART"]
                dtstart = datetime.strptime(dtstart_str, "%Y-%m-%d")

            # Parse UNTIL if present
            until = None
            if "UNTIL" in rrule_dict:
                until_str = rrule_dict["UNTIL"]
                until = datetime.strptime(until_str, "%Y-%m-%d")

            # Parse BYDAY if present (convert to list of rrule weekday objects)
            byweekday = None
            if "BYDAY" in rrule_dict:
                byday_str = rrule_dict["BYDAY"]  # e.g., "MO,WE,FR"
                weekday_map = {
                    "MO": rrule.MO,
                    "TU": rrule.TU,
                    "WE": rrule.WE,
                    "TH": rrule.TH,
                    "FR": rrule.FR,
                    "SA": rrule.SA,
                    "SU": rrule.SU,
                }
                byweekday = [
                    weekday_map[day.strip()]
                    for day in byday_str.split(",")
                    if day.strip() in weekday_map
                ]

            return rrule.rrule(
                freq=freq,
                dtstart=dtstart or datetime.now(),
                until=until,
                byweekday=byweekday,
            )

        except Exception as e:
            logger.error(f"Failed to parse recurrence rule: {e}")
            return None
