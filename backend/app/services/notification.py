"""
Notification service for managing user notifications.
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.models import (
    Notification,
    NotificationType,
    User,
)
from app.schemas_module import NotificationResponse

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications."""

    @staticmethod
    async def create_notification(
        session: AsyncSession,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        related_id: UUID | None = None,
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            related_id=related_id,
        )

        session.add(notification)
        await session.flush()

        logger.info(f"Created notification {notification.id} for user {user_id}")

        return notification

    @staticmethod
    async def mark_read(
        session: AsyncSession,
        notification_id: UUID,
    ) -> Notification:
        """Mark notification as read."""
        notification = await session.get(Notification, notification_id)

        if notification:
            notification.read_at = datetime.utcnow()
            await session.flush()

        return notification

    @staticmethod
    async def mark_sent(
        session: AsyncSession,
        notification_id: UUID,
    ) -> Notification:
        """Mark notification as sent (for async delivery)."""
        notification = await session.get(Notification, notification_id)

        if notification:
            notification.sent_at = datetime.utcnow()
            await session.flush()

        return notification

    @staticmethod
    async def get_user_notifications(
        session: AsyncSession,
        user_id: UUID,
        unread_only: bool = False,
    ) -> list[Notification]:
        """Get notifications for a user."""
        stmt = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            stmt = stmt.where(Notification.read_at == None)

        # Order by created_at descending (newest first)
        stmt = stmt.order_by(Notification.created_at.desc())

        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def delete_notification(
        session: AsyncSession,
        notification_id: UUID,
    ) -> bool:
        """Delete a notification."""
        notification = await session.get(Notification, notification_id)

        if notification:
            await session.delete(notification)
            return True

        return False
