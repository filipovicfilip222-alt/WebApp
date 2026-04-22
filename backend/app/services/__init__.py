"""
Services module for business logic.
"""

from app.services.auth import auth_service, AuthService, get_current_user, get_current_user_with_role
from app.services.availability import AvailabilityService
from app.services.redis_service import RedisService, create_redis_client, get_redis_service
from app.services.appointment import AppointmentService
from app.services.notification import NotificationService
from app.services.storage import StorageService, storage_service
from app.services.ws_manager import ChatConnectionManager, chat_manager

__all__ = [
    "auth_service",
    "AuthService",
    "get_current_user",
    "get_current_user_with_role",
    "AvailabilityService",
    "RedisService",
    "create_redis_client",
    "get_redis_service",
    "AppointmentService",
    "NotificationService",
    "StorageService",
    "storage_service",
    "ChatConnectionManager",
    "chat_manager",
]
