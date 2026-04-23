"""
API endpoints for availability slots management.
"""

from datetime import datetime, date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.database import get_db
from app.services import (
    get_current_user,
    AvailabilityService,
)
from app.schemas_module import (
    KeycloakUserInfo,
    AvailabilitySlotResponse,
    AvailabilitySlotCreate,
    AvailabilitySlotUpdate,
    ExpandedSlot,
)
from app.models.models import AvailabilitySlot

router = APIRouter(
    prefix="/v1/availability",
    tags=["availability"],
)


@router.post(
    "/slots",
    response_model=AvailabilitySlotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_availability_slot(
    slot_data: AvailabilitySlotCreate,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Create an availability slot.
    
    Professor creates recurring availability for consultations.
    Slot defines day of week, time, max students, and recurrence rule.
    """
    # Only professors/assistants can create slots
    user_roles = getattr(user, "realm_access", {}).get("roles", [])
    if not any(role in user_roles for role in ["PROFESOR", "ASISTENT"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors/assistants can create availability slots",
        )

    professor_id = UUID(user.sub)

    # Generate default recurrence rule if not provided
    rrule = slot_data.recurrence_rule or await AvailabilityService.create_recurrence_rule(
        slot_data.day_of_week
    )

    slot = AvailabilitySlot(
        professor_id=professor_id,
        day_of_week=slot_data.day_of_week,
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
        max_students=slot_data.max_students,
        type=slot_data.type,
        recurrence_rule=rrule,
        is_active=True,
    )

    session.add(slot)
    await session.commit()

    return slot


@router.get(
    "/slots/my",
    response_model=list[AvailabilitySlotResponse],
)
async def get_my_availability_slots(
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get current professor's availability slots."""
    professor_id = UUID(user.sub)

    stmt = select(AvailabilitySlot).where(
        AvailabilitySlot.professor_id == professor_id
    )
    result = await session.execute(stmt)
    slots = result.scalars().all()

    return slots


@router.get(
    "/slots/{professor_id}",
    response_model=list[AvailabilitySlotResponse],
)
async def get_professor_availability_slots(
    professor_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """Get a professor's availability slots (public view)."""
    stmt = select(AvailabilitySlot).where(
        and_(
            AvailabilitySlot.professor_id == professor_id,
            AvailabilitySlot.is_active == True,
        )
    )
    result = await session.execute(stmt)
    slots = result.scalars().all()

    return slots


@router.patch(
    "/slots/{slot_id}",
    response_model=AvailabilitySlotResponse,
)
async def update_availability_slot(
    slot_id: UUID,
    update_data: AvailabilitySlotUpdate,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Update an availability slot."""
    slot = await session.get(AvailabilitySlot, slot_id)

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot not found",
        )

    professor_id = UUID(user.sub)

    if slot.professor_id != professor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only modify own slots",
        )

    if update_data.max_students is not None:
        slot.max_students = update_data.max_students
    if update_data.type is not None:
        slot.type = update_data.type
    if update_data.recurrence_rule is not None:
        slot.recurrence_rule = update_data.recurrence_rule
    if update_data.is_active is not None:
        slot.is_active = update_data.is_active

    await session.commit()

    return slot


@router.delete(
    "/slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_availability_slot(
    slot_id: UUID,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Delete an availability slot."""
    slot = await session.get(AvailabilitySlot, slot_id)

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot not found",
        )

    professor_id = UUID(user.sub)

    if slot.professor_id != professor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete own slots",
        )

    await session.delete(slot)
    await session.commit()


@router.get(
    "/expanded/{professor_id}",
    response_model=list[ExpandedSlot],
)
async def get_expanded_availability(
    professor_id: UUID,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    available_only: bool = Query(True, description="Only show available slots"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get expanded availability slots for a professor over a date range.
    
    Returns individual slot instances accounting for recurrence and blackouts.
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date",
        )

    if (end_date - start_date).days > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 90 days",
        )

    expanded = await AvailabilityService.get_available_slots(
        session=session,
        professor_id=professor_id,
        start_date=start_date,
        end_date=end_date,
        include_full=not available_only,
    )

    return expanded


@router.get(
    "/search",
    response_model=list[ExpandedSlot],
)
async def search_availability(
    professor_id: UUID = Query(None, description="Filter by professor"),
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    appointment_type: str = Query(None, description="Filter by type (UZIVO/ONLINE)"),
    session: AsyncSession = Depends(get_db),
):
    """
    Search for available consultation slots.
    
    Students use this to find and book with professors.
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date",
        )

    if (end_date - start_date).days > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 90 days",
        )

    # If professor_id provided, get only their slots
    if professor_id:
        expanded = await AvailabilityService.get_available_slots(
            session=session,
            professor_id=professor_id,
            start_date=start_date,
            end_date=end_date,
        )
    else:
        # Search across all professors (can be expensive!)
        # For now, return empty - would need proper indexing in production
        expanded = []

    # Filter by appointment type if specified
    if appointment_type:
        expanded = [s for s in expanded if s.type.value == appointment_type]

    return expanded
