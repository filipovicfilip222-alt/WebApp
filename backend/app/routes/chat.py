"""
Chat endpoints (HTTP + WebSocket) for appointment conversations.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db, async_session
from app.models.models import Appointment, TicketChatMessage
from app.schemas import KeycloakUserInfo, TicketChatMessageCreate, TicketChatMessageResponse
from app.services import get_current_user
from app.services.auth import auth_service
from app.services.ws_manager import chat_manager

router = APIRouter(prefix="/v1/chat", tags=["chat"])


def _can_access_appointment(appointment: Appointment, user_id: UUID, user_roles: list[str]) -> bool:
    return (
        appointment.student_id == user_id
        or appointment.professor_id == user_id
        or "ADMIN" in user_roles
    )


@router.get("/appointments/{appointment_id}/messages", response_model=list[TicketChatMessageResponse])
async def get_messages(
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
        select(TicketChatMessage)
        .where(TicketChatMessage.appointment_id == appointment_id)
        .order_by(TicketChatMessage.sent_at.asc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/appointments/{appointment_id}/messages", response_model=TicketChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def post_message(
    appointment_id: UUID,
    payload: TicketChatMessageCreate,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    if payload.appointment_id != appointment_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment id mismatch")

    appointment = await session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    user_id = UUID(user.sub)
    roles = (user.realm_access or {}).get("roles", [])
    if not _can_access_appointment(appointment, user_id, roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    message = TicketChatMessage(
        appointment_id=appointment_id,
        user_id=user_id,
        message=payload.message,
        sent_at=datetime.utcnow(),
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)

    await chat_manager.broadcast(
        appointment_id,
        {
            "event": "chat.message",
            "data": {
                "id": str(message.id),
                "appointment_id": str(message.appointment_id),
                "user_id": str(message.user_id),
                "message": message.message,
                "sent_at": message.sent_at.isoformat(),
            },
        },
    )

    return message


@router.websocket("/ws/appointments/{appointment_id}")
async def chat_socket(
    websocket: WebSocket,
    appointment_id: UUID,
    token: str = Query(...),
):
    user = await auth_service.validate_token(token)
    if not user:
        await websocket.close(code=1008)
        return

    user_id = UUID(user.sub)
    roles = (user.realm_access or {}).get("roles", [])

    async with async_session() as session:
        appointment = await session.get(Appointment, appointment_id)
        if not appointment:
            await websocket.close(code=1008)
            return

        if not _can_access_appointment(appointment, user_id, roles):
            await websocket.close(code=1008)
            return

    await chat_manager.connect(appointment_id, websocket)
    try:
        while True:
            raw = await websocket.receive_json()
            text = str(raw.get("message", "")).strip()
            if not text:
                continue

            async with async_session() as session:
                message = TicketChatMessage(
                    appointment_id=appointment_id,
                    user_id=user_id,
                    message=text,
                    sent_at=datetime.utcnow(),
                )
                session.add(message)
                await session.commit()
                await session.refresh(message)

            await chat_manager.broadcast(
                appointment_id,
                {
                    "event": "chat.message",
                    "data": {
                        "id": str(message.id),
                        "appointment_id": str(message.appointment_id),
                        "user_id": str(message.user_id),
                        "message": message.message,
                        "sent_at": message.sent_at.isoformat(),
                    },
                },
            )
    except WebSocketDisconnect:
        chat_manager.disconnect(appointment_id, websocket)
