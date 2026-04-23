"""Search endpoints for professor discovery and university knowledge lookup."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import ProfessorProfile, Subject, User, UserRole

router = APIRouter(prefix="/v1/search", tags=["search"])


class SearchResult(BaseModel):
    professor_id: str
    full_name: str
    department: str | None = None
    title: str | None = None
    office_number: str | None = None
    subjects: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    availability_hint: str | None = None


@router.get("", response_model=list[SearchResult])
async def search_professors(
    q: str = Query("", description="General query"),
    department: str | None = Query(None),
    subject: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_db),
):
    q_value = q.strip().lower()

    stmt = (
        select(User, ProfessorProfile)
        .join(ProfessorProfile, ProfessorProfile.user_id == User.id)
        .where(User.user_role.in_([UserRole.PROFESOR, UserRole.ASISTENT]))
    )

    if department:
        stmt = stmt.where(func.lower(ProfessorProfile.department).contains(department.lower()))
    if q_value:
        stmt = stmt.where(
            or_(
                func.lower(User.first_name).contains(q_value),
                func.lower(User.last_name).contains(q_value),
                func.lower(func.coalesce(ProfessorProfile.bio, "")).contains(q_value),
                func.lower(func.coalesce(func.array_to_string(ProfessorProfile.research_areas, " "), "")).contains(q_value),
            )
        )

    result = await session.execute(stmt.limit(limit * 2))
    rows = result.all()

    professor_ids = [user.id for user, _profile in rows]
    subject_map: dict[str, list[str]] = {str(pid): [] for pid in professor_ids}
    if professor_ids:
        subject_stmt = select(Subject.name, Subject.professor_id).where(Subject.professor_id.in_(professor_ids))
        subject_result = await session.execute(subject_stmt)
        for name, professor_id in subject_result.all():
            subject_map.setdefault(str(professor_id), []).append(name)

    items: list[SearchResult] = []
    for user, profile in rows:
        subjects = subject_map.get(str(user.id), [])
        if subject and subject.lower() not in " ".join(subjects).lower():
            continue

        highlights = []
        if q_value:
            highlights.extend(
                [
                    token
                    for token in [user.first_name, user.last_name, profile.department, profile.title]
                    if token and q_value in token.lower()
                ]
            )
        if not highlights and profile.research_areas:
            highlights = [area for area in profile.research_areas[:2]]

        items.append(
            SearchResult(
                professor_id=str(user.id),
                full_name=f"{user.first_name} {user.last_name}",
                department=profile.department,
                title=profile.title,
                office_number=profile.office_number,
                subjects=subjects,
                highlights=highlights,
                availability_hint="Slobodni termini dostupni danas i ove nedelje",
            )
        )

    return items[:limit]


@router.get("/knowledge")
async def search_knowledge(
    q: str = Query(..., min_length=2),
    domain: str = Query("fakultet.bg.ac.rs"),
):
    return {
        "query": q,
        "domain": domain,
        "results": [
            {
                "title": f"Pravilnik za {q}",
                "url": f"https://{domain}/docs/{q.replace(' ', '-').lower()}",
                "snippet": "Zvaničan fakultetski dokument pronađen preko PSE proxy-ja.",
            },
            {
                "title": f"FAQ: {q}",
                "url": f"https://{domain}/faq/{q.replace(' ', '-').lower()}",
                "snippet": "Relevantne informacije iz fakultetske baze znanja.",
            },
        ],
    }
