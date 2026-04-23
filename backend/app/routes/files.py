"""
Appointment file upload/list endpoints backed by MinIO.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db
from app.models.models import Appointment, AppointmentFile
from app.schemas_module import AppointmentFileDownloadResponse, AppointmentFileResponse, KeycloakUserInfo
from app.services import get_current_user
from app.services.storage import storage_service

router = APIRouter(prefix="/v1/files", tags=["files"])


def _can_access_appointment(appointment: Appointment, user_id: UUID, user_roles: list[str]) -> bool:
    return (
        appointment.student_id == user_id
        or appointment.professor_id == user_id
        or "ADMIN" in user_roles
    )


@router.post("/appointments/{appointment_id}/upload", response_model=AppointmentFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_appointment_file(
    appointment_id: UUID,
    file: UploadFile = File(...),
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    appointment = await session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    user_id = UUID(user.sub)
    roles = (user.realm_access or {}).get("roles", [])
    if not _can_access_appointment(appointment, user_id, roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    data = await file.read()
    max_bytes = settings.appointment_max_files_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large")

    existing_stmt = select(AppointmentFile).where(AppointmentFile.appointment_id == appointment_id)
    existing = (await session.execute(existing_stmt)).scalars().all()
    if len(existing) >= settings.appointment_max_files_per_appointment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File limit reached")

    path = storage_service.upload_appointment_file(
        appointment_id=appointment_id,
        original_name=file.filename,
        content=data,
        content_type=file.content_type,
    )

    record = AppointmentFile(
        appointment_id=appointment_id,
        minio_path=path,
        file_name=file.filename,
        file_size=len(data),
        uploaded_by=user_id,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


@router.get("/appointments/{appointment_id}", response_model=list[AppointmentFileResponse])
async def list_appointment_files(
    appointment_id: UUID,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    appointment = await session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    user_id = UUID(user.sub)
    roles = (user.realm_access or {}).get("roles", [])
    if not _can_access_appointment(appointment, user_id, roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    stmt = (
        select(AppointmentFile)
        .where(AppointmentFile.appointment_id == appointment_id)
        .order_by(AppointmentFile.created_at.asc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get(
    "/appointments/{appointment_id}/{file_id}/download-url",
    response_model=AppointmentFileDownloadResponse,
)
async def get_appointment_file_download_url(
    appointment_id: UUID,
    file_id: UUID,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    appointment = await session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    user_id = UUID(user.sub)
    roles = (user.realm_access or {}).get("roles", [])
    if not _can_access_appointment(appointment, user_id, roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    file_record = await session.get(AppointmentFile, file_id)
    if not file_record or file_record.appointment_id != appointment_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    expires_in = 15 * 60
    try:
        download_url = storage_service.presigned_download_url(file_record.minio_path, expires_seconds=expires_in)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid storage path")

    return AppointmentFileDownloadResponse(
        file_id=file_record.id,
        file_name=file_record.file_name,
        download_url=download_url,
        expires_in_seconds=expires_in,
    )
