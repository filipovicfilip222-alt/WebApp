"""
Redis utilities for distributed locks and slot management.
Implements pessimistic locking to prevent double-booking.
"""

import logging
import json
from typing import Optional
import uuid

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Service for Redis operations including pessimistic locking."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def acquire_slot_lock(
        self,
        slot_id: str,
        user_id: str,
        ttl_seconds: int = 30,
    ) -> Optional[str]:
        """
        Acquire exclusive lock for a slot.
        
        Uses SET NX (set if not exists) with expiration.
        Returns lock token if acquired, None if lock already held.
        
        Args:
            slot_id: Availability slot ID
            user_id: Student ID requesting lock
            ttl_seconds: How long to hold the lock (default 30s)
            
        Returns:
            Lock token if successful, None otherwise
        """
        lock_key = f"slot_lock:{slot_id}"
        lock_token = str(uuid.uuid4())
        lock_value = json.dumps({
            "user_id": user_id,
            "token": lock_token,
        })

        try:
            acquired = await self.redis.set(
                lock_key,
                lock_value,
                ex=ttl_seconds,
                nx=True,  # Only set if doesn't exist
            )
            return lock_token if acquired else None
        except Exception as e:
            logger.error(f"Failed to acquire slot lock: {e}")
            return None

    async def release_slot_lock(
        self,
        slot_id: str,
        lock_token: str,
    ) -> bool:
        """
        Release lock for a slot (only if token matches).
        
        Args:
            slot_id: Availability slot ID
            lock_token: Lock token from acquire_slot_lock
            
        Returns:
            True if released, False otherwise
        """
        lock_key = f"slot_lock:{slot_id}"

        try:
            # Lua script to ensure atomic compare-and-delete
            lua_script = """
            local lock_key = KEYS[1]
            local lock_token = ARGV[1]
            local current = redis.call('GET', lock_key)
            if current then
                local lock_data = cjson.decode(current)
                if lock_data.token == lock_token then
                    redis.call('DEL', lock_key)
                    return 1
                end
            end
            return 0
            """
            result = await self.redis.eval(lua_script, 1, lock_key, lock_token)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to release slot lock: {e}")
            return False

    async def push_to_waitlist(
        self,
        slot_id: str,
        student_id: str,
    ) -> int:
        """
        Add student to slot waitlist (Redis list).
        
        Args:
            slot_id: Availability slot ID
            student_id: Student ID
            
        Returns:
            Position in waitlist (0-indexed)
        """
        waitlist_key = f"waitlist:{slot_id}"

        try:
            length = await self.redis.rpush(waitlist_key, student_id)
            # Set expiration (30 days)
            await self.redis.expire(waitlist_key, 30 * 24 * 60 * 60)
            return length - 1  # 0-indexed position
        except Exception as e:
            logger.error(f"Failed to push to waitlist: {e}")
            return -1

    async def get_waitlist_position(
        self,
        slot_id: str,
        student_id: str,
    ) -> Optional[int]:
        """
        Get student's position in waitlist.
        
        Returns:
            0-indexed position, or None if not in waitlist
        """
        waitlist_key = f"waitlist:{slot_id}"

        try:
            # Get all students in waitlist
            students = await self.redis.lrange(waitlist_key, 0, -1)
            students = [s.decode() if isinstance(s, bytes) else s for s in students]
            
            if str(student_id) in students:
                return students.index(str(student_id))
            return None
        except Exception as e:
            logger.error(f"Failed to get waitlist position: {e}")
            return None

    async def pop_from_waitlist(
        self,
        slot_id: str,
    ) -> Optional[str]:
        """
        Remove and return next student from waitlist.
        
        Returns:
            Student ID, or None if waitlist empty
        """
        waitlist_key = f"waitlist:{slot_id}"

        try:
            student_id = await self.redis.lpop(waitlist_key)
            return student_id.decode() if isinstance(student_id, bytes) else student_id
        except Exception as e:
            logger.error(f"Failed to pop from waitlist: {e}")
            return None

    async def store_appointment_in_progress(
        self,
        student_id: str,
        appointment_data: dict,
        ttl_seconds: int = 300,  # 5 minutes
    ) -> bool:
        """
        Store appointment booking data temporarily (for transaction handling).
        
        Args:
            student_id: Student ID
            appointment_data: Dict with appointment details
            ttl_seconds: TTL in seconds
            
        Returns:
            True if stored, False otherwise
        """
        key = f"appointment_in_progress:{student_id}"
        
        try:
            await self.redis.setex(
                key,
                ttl_seconds,
                json.dumps(appointment_data),
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store appointment in progress: {e}")
            return False

    async def get_appointment_in_progress(
        self,
        student_id: str,
    ) -> Optional[dict]:
        """
        Retrieve stored appointment booking data.
        
        Returns:
            Dict with appointment data, or None
        """
        key = f"appointment_in_progress:{student_id}"
        
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get appointment in progress: {e}")
            return None

    async def clear_appointment_in_progress(
        self,
        student_id: str,
    ) -> bool:
        """
        Clear stored appointment booking data.
        
        Returns:
            True if deleted, False otherwise
        """
        key = f"appointment_in_progress:{student_id}"
        
        try:
            deleted = await self.redis.delete(key)
            return bool(deleted)
        except Exception as e:
            logger.error(f"Failed to clear appointment in progress: {e}")
            return False

    async def store_notification(
        self,
        user_id: str,
        notification_data: dict,
        ttl_seconds: int = 7 * 24 * 60 * 60,  # 7 days
    ) -> bool:
        """
        Store notification in Redis for later retrieval (as backup to DB).
        
        Args:
            user_id: User ID
            notification_data: Dict with notification details
            ttl_seconds: TTL in seconds
            
        Returns:
            True if stored, False otherwise
        """
        key = f"notifications:{user_id}"
        
        try:
            notification_id = notification_data.get("id", str(uuid.uuid4()))
            await self.redis.hset(
                key,
                notification_id,
                json.dumps(notification_data),
            )
            await self.redis.expire(key, ttl_seconds)
            return True
        except Exception as e:
            logger.error(f"Failed to store notification: {e}")
            return False

    async def get_user_notifications(
        self,
        user_id: str,
    ) -> list[dict]:
        """
        Retrieve all pending notifications for a user.
        
        Returns:
            List of notification dicts
        """
        key = f"notifications:{user_id}"
        
        try:
            data = await self.redis.hgetall(key)
            notifications = []
            for notification_json in data.values():
                notifications.append(json.loads(notification_json))
            return notifications
        except Exception as e:
            logger.error(f"Failed to get user notifications: {e}")
            return []

    async def publish_event(
        self,
        channel: str,
        event_data: dict,
    ) -> int:
        """
        Publish event to Redis Pub/Sub channel.
        Used for real-time updates (chat, notifications).
        
        Args:
            channel: Channel name
            event_data: Event data dict
            
        Returns:
            Number of subscribers
        """
        try:
            num_subscribers = await self.redis.publish(
                channel,
                json.dumps(event_data),
            )
            return num_subscribers
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return 0


# Factory function for creating Redis client
async def create_redis_client() -> redis.Redis:
    """Create and return Redis async client."""
    return redis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
        encoding="utf-8",
        decode_responses=True,
    )


async def get_redis_service(redis_client: redis.Redis = None) -> RedisService:
    """
    Dependency for getting RedisService.
    
    Usage:
        @router.post("/appointments")
        async def book_appointment(
            redis_svc: RedisService = Depends(get_redis_service)
        ):
            ...
    """
    if redis_client is None:
        redis_client = await create_redis_client()
    return RedisService(redis_client)
