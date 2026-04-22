"""
SQLAlchemy declarative base and mixin classes.
"""

from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import DateTime, func
from datetime import datetime
from uuid import UUID, uuid4

# Declarative base for all models
Base = declarative_base()


class BaseModel:
    """Base mixin for common columns."""
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
