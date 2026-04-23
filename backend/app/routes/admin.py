"""Admin endpoints for user management, impersonation and broadcasts."""

from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import AuditAction, AuditLog, Notification, NotificationType, User, UserRole
from app.schemas_module import KeycloakUserInfo, UserCreate, UserResponse, UserUpdate
from app.services import get_current_user

router = APIRouter(prefix="/v1/admin", tags=["admin"])


class BroadcastPayload(BaseModel):
    title: str = Field(..., min_length=3)
    message: str = Field(..., min_length=5)
    audience: str = Field(default="all")
    target_role: str | None = None
    target_department: str | None = None
    delay_minutes: int = Field(default=0, ge=0, le=300)


class ImpersonationResponse(BaseModel):
    user_id: str
    display_name: str
    role: str
    audit_log_id: str


class ImportPreviewRow(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    student_index: str | None = None
    study_program: str | None = None


class ImportSummary(BaseModel):
    created: int
    skipped: int
    preview: list[ImportPreviewRow]


def _ensure_admin(user: KeycloakUserInfo) -> None:
    roles = (user.realm_access or {}).get("roles", [])
    if "ADMIN" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    role: UserRole | None = None,
    session: AsyncSession = Depends(get_db),
    user: KeycloakUserInfo = Depends(get_current_user),
):
    _ensure_admin(user)
    stmt = select(User)
    if role:
        stmt = stmt.where(User.user_role == role)
    result = await session.execute(stmt.order_by(User.last_name.asc(), User.first_name.asc()))
    return result.scalars().all()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db),
    user: KeycloakUserInfo = Depends(get_current_user),
):
    _ensure_admin(user)
    record = User(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        user_role=payload.user_role,
        keycloak_id=payload.keycloak_id,
        is_active=True,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    session: AsyncSession = Depends(get_db),
    user: KeycloakUserInfo = Depends(get_current_user),
):
    _ensure_admin(user)
    record = await session.get(User, user_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await session.commit()
    await session.refresh(record)
    return record


@router.post("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: KeycloakUserInfo = Depends(get_current_user),
):
    _ensure_admin(user)
    record = await session.get(User, user_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    record.is_active = False
    await session.commit()
    await session.refresh(record)
    return record


@router.post("/import/students", response_model=ImportSummary)
async def bulk_import_students(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    user: KeycloakUserInfo = Depends(get_current_user),
):
    _ensure_admin(user)
    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(StringIO(content))
    preview: list[ImportPreviewRow] = []
    created = 0
    skipped = 0

    for row in reader:
        email = (row.get("email") or "").strip().lower()
        first_name = (row.get("first_name") or row.get("ime") or "").strip()
        last_name = (row.get("last_name") or row.get("prezime") or "").strip()
        if not email or not first_name or not last_name:
            skipped += 1
            continue
        preview.append(
            ImportPreviewRow(
                email=email,
                first_name=first_name,
                last_name=last_name,
                student_index=row.get("student_index") or row.get("indeks"),
                study_program=row.get("study_program") or row.get("smer"),
            )
        )
        exists = await session.execute(select(User).where(User.email == email))
        if exists.scalar_one_or_none():
            skipped += 1
            continue
        session.add(
            User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                user_role=UserRole.STUDENT,
                is_active=True,
            )
        )
        created += 1

    await session.commit()
    return ImportSummary(created=created, skipped=skipped, preview=preview[:10])


@router.post("/impersonate/{target_user_id}", response_model=ImpersonationResponse)
async def impersonate_user(
    target_user_id: UUID,
    request_user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    _ensure_admin(request_user)
    target = await session.get(User, target_user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    audit = AuditLog(
        admin_id=UUID(request_user.sub),
        action=AuditAction.LOGIN_AS,
        target_user_id=target_user_id,
        details={"display_name": f"{target.first_name} {target.last_name}"},
        started_at=datetime.utcnow(),
        ended_at=None,
    )
    session.add(audit)
    await session.commit()
    await session.refresh(audit)

    return ImpersonationResponse(
        user_id=str(target_user_id),
        display_name=f"{target.first_name} {target.last_name}",
        role=target.user_role.value if hasattr(target.user_role, "value") else str(target.user_role),
        audit_log_id=str(audit.id),
    )


@router.post("/broadcast")
async def broadcast_message(
    payload: BroadcastPayload,
    session: AsyncSession = Depends(get_db),
    user: KeycloakUserInfo = Depends(get_current_user),
):
    _ensure_admin(user)
    result = await session.execute(select(User).where(User.is_active == True))
    recipients = result.scalars().all()

    for recipient in recipients:
        session.add(
            Notification(
                user_id=recipient.id,
                notification_type=NotificationType.IN_APP,
                title=payload.title,
                message=payload.message,
                sent_at=datetime.utcnow(),
            )
        )

    await session.commit()

    return {
        "status": "scheduled",
        "recipient_count": len(recipients),
        "audience": payload.audience,
        "delay_minutes": payload.delay_minutes,
    }
