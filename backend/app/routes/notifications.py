"""
API endpoints for notifications.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services import get_current_user
from app.schemas import (
    KeycloakUserInfo,
    NotificationResponse,
)
from app.services.notification import NotificationService
from app.models.models import Notification

router = APIRouter(
    prefix="/v1/notifications",
    tags=["notifications"],
)


@router.get(
    "/my",
    response_model=list[NotificationResponse],
)
async def get_my_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get current user's notifications."""
    user_id = UUID(user.sub)

    notifications = await NotificationService.get_user_notifications(
        session, user_id, unread_only=unread_only
    )

    return notifications[:limit]


@router.post(
    "/{notification_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def mark_notification_read(
    notification_id: UUID,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Mark notification as read."""
    user_id = UUID(user.sub)

    notification = await session.get(Notification, notification_id)

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    if notification.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to mark this notification",
        )

    await NotificationService.mark_read(session, notification_id)
    await session.commit()


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_notification(
    notification_id: UUID,
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Delete a notification."""
    user_id = UUID(user.sub)

    notification = await session.get(Notification, notification_id)

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    if notification.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this notification",
        )

    await NotificationService.delete_notification(session, notification_id)
    await session.commit()


@router.post(
    "/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def mark_all_notifications_read(
    user: KeycloakUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Mark all user's notifications as read."""
    from sqlalchemy import update
    from datetime import datetime

    user_id = UUID(user.sub)

    stmt = update(Notification).where(
        Notification.user_id == user_id
    ).values(read_at=datetime.utcnow())

    await session.execute(stmt)
    await session.commit()
