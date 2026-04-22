"""
Celery application setup for background tasks.
Run with: celery -A app.tasks.celery_app worker --loglevel=info
"""

from celery import Celery
from app.config import settings

celery_app = Celery(
    "studentska_platforma",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Load Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Belgrade",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


# Placeholder for background tasks
# Phase 1 tasks:
# - send_email_task
# - check_no_shows_task
# - notify_waitlist_task
# - broadcast_notification_task
