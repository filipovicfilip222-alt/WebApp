"""
API endpoints for strike management (admin only).
"""

from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.services import get_current_user, get_current_user_with_role
from app.schemas import (
    KeycloakUserInfo,
    StrikeRecordResponse,
)
from app.models.models import (
    StrikeRecord,
    StudentProfile,
)

router = APIRouter(
    prefix="/v1/admin/strikes",
    tags=["strikes"],
)


@router.get(
    "/student/{student_id}",
    response_model=list[StrikeRecordResponse],
)
async def get_student_strikes(
    student_id: UUID,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Get all strikes for a student.
    
    Accessible by: admin, professor of the student, student themselves.
    """
    user_id = UUID(user.sub)
    user_roles = getattr(user, "realm_access", {}).get("roles", [])

    # Check permissions
    is_admin = "ADMIN" in user_roles
    is_same_student = student_id == user_id

    if not (is_admin or is_same_student):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these strikes",
        )

    stmt = select(StrikeRecord).where(
        StrikeRecord.student_id == student_id
    )
    result = await session.execute(stmt)
    strikes = result.scalars().all()

    return strikes


@router.post(
    "/student/{student_id}/remove/{strike_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_strike(
    student_id: UUID,
    strike_id: UUID,
    reason: str = None,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Remove a strike (admin only).
    
    Logs the removal in audit log.
    """
    user_id = UUID(user.sub)
    user_roles = getattr(user, "realm_access", {}).get("roles", [])

    # Only admin can remove strikes
    if "ADMIN" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can remove strikes",
        )

    strike = await session.get(StrikeRecord, strike_id)

    if not strike:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strike not found",
        )

    if strike.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Strike ID does not match student",
        )

    # Mark strike as removed
    strike.removed_at = datetime.utcnow()
    strike.removed_by = user_id
    strike.removed_reason = reason

    # Update student strike count
    stmt = select(StudentProfile).where(StudentProfile.user_id == student_id)
    result = await session.execute(stmt)
    student_profile = result.scalar()

    if student_profile:
        student_profile.strike_count = max(0, student_profile.strike_count - strike.points)

    await session.commit()


@router.get(
    "/active",
    response_model=list[StrikeRecordResponse],
)
async def get_active_strikes(
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Get all active (non-expired, non-removed) strikes.
    
    Admin only.
    """
    from datetime import datetime

    user_roles = getattr(user, "realm_access", {}).get("roles", [])

    if "ADMIN" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can view all strikes",
        )

    now = datetime.utcnow()

    stmt = select(StrikeRecord).where(
        StrikeRecord.removed_at == None,
        StrikeRecord.expires_at > now,
    )
    result = await session.execute(stmt)
    strikes = result.scalars().all()

    return strikes


@router.post(
    "/student/{student_id}/block",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def block_student(
    student_id: UUID,
    reason: str = None,
    until_date: str = None,  # Optional: "2026-05-30"
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Block a student from booking (admin only).
    
    Prevents student from creating new appointments.
    """
    user_roles = getattr(user, "realm_access", {}).get("roles", [])

    if "ADMIN" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can block students",
        )

    stmt = select(StudentProfile).where(StudentProfile.user_id == student_id)
    result = await session.execute(stmt)
    student_profile = result.scalar()

    if not student_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    student_profile.is_blocked = True

    if until_date:
        student_profile.blocked_until = datetime.strptime(until_date, "%Y-%m-%d")

    await session.commit()


@router.post(
    "/student/{student_id}/unblock",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unblock_student(
    student_id: UUID,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Unblock a student (admin only)."""
    user_roles = getattr(user, "realm_access", {}).get("roles", [])

    if "ADMIN" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can unblock students",
        )

    stmt = select(StudentProfile).where(StudentProfile.user_id == student_id)
    result = await session.execute(stmt)
    student_profile = result.scalar()

    if not student_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    student_profile.is_blocked = False
    student_profile.blocked_until = None

    await session.commit()
