"""
API endpoints for user management and profiles.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.services import get_current_user
from app.schemas_module import (
    KeycloakUserInfo,
    UserResponse,
    UserDetailResponse,
    StudentProfileResponse,
    StudentProfileUpdate,
    ProfessorProfileResponse,
    ProfessorProfileUpdate,
)
from app.models.models import (
    User,
    StudentProfile,
    ProfessorProfile,
    UserRole,
)

router = APIRouter(
    prefix="/v1/users",
    tags=["users"],
)


@router.get(
    "/me",
    response_model=UserDetailResponse,
)
async def get_current_user_profile(
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get current user's profile."""
    user_id = UUID(user.sub)

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    db_user = result.scalar()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    return db_user


@router.get(
    "/{user_id}",
    response_model=UserDetailResponse,
)
async def get_user_profile(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """Get user profile (public view)."""
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    db_user = result.scalar()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return db_user


@router.get(
    "/profile/student",
    response_model=StudentProfileResponse,
)
async def get_student_profile(
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get current user's student profile."""
    user_id = UUID(user.sub)

    stmt = select(StudentProfile).where(StudentProfile.user_id == user_id)
    result = await session.execute(stmt)
    profile = result.scalar()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    return profile


@router.patch(
    "/profile/student",
    response_model=StudentProfileResponse,
)
async def update_student_profile(
    update_data: StudentProfileUpdate,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Update current user's student profile."""
    user_id = UUID(user.sub)

    stmt = select(StudentProfile).where(StudentProfile.user_id == user_id)
    result = await session.execute(stmt)
    profile = result.scalar()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    if update_data.student_index is not None:
        profile.student_index = update_data.student_index
    if update_data.study_program is not None:
        profile.study_program = update_data.study_program
    if update_data.year_enrolled is not None:
        profile.year_enrolled = update_data.year_enrolled

    await session.commit()

    return profile


@router.get(
    "/profile/professor",
    response_model=ProfessorProfileResponse,
)
async def get_professor_profile(
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get current user's professor profile."""
    user_id = UUID(user.sub)

    stmt = select(ProfessorProfile).where(ProfessorProfile.user_id == user_id)
    result = await session.execute(stmt)
    profile = result.scalar()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor profile not found",
        )

    return profile


@router.patch(
    "/profile/professor",
    response_model=ProfessorProfileResponse,
)
async def update_professor_profile(
    update_data: ProfessorProfileUpdate,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Update current user's professor profile."""
    user_id = UUID(user.sub)

    stmt = select(ProfessorProfile).where(ProfessorProfile.user_id == user_id)
    result = await session.execute(stmt)
    profile = result.scalar()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor profile not found",
        )

    if update_data.office_number is not None:
        profile.office_number = update_data.office_number
    if update_data.title is not None:
        profile.title = update_data.title
    if update_data.department is not None:
        profile.department = update_data.department
    if update_data.avatar_url is not None:
        profile.avatar_url = update_data.avatar_url
    if update_data.bio is not None:
        profile.bio = update_data.bio
    if update_data.research_areas is not None:
        profile.research_areas = update_data.research_areas
    if update_data.publications_link is not None:
        profile.publications_link = update_data.publications_link

    await session.commit()

    return profile


@router.get(
    "/{user_id}/profile/professor",
    response_model=ProfessorProfileResponse,
)
async def get_professor_profile_public(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """Get a professor's profile (public view)."""
    stmt = select(ProfessorProfile).where(ProfessorProfile.user_id == user_id)
    result = await session.execute(stmt)
    profile = result.scalar()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor profile not found",
        )

    return profile
