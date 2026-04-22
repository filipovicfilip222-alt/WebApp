#!/usr/bin/env python
"""
Seed database with development data.
Run after migrations: python scripts/seed_dev_data.py
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import settings
from app.db.database import engine as db_engine
from app.db.base import Base
from uuid import uuid4


# For now, just a placeholder. In Phase 1, we'll add:
# - 2 Admin users
# - 5 Professor users with profiles
# - 50 Student users with profiles
# - 10 Subjects with professor/assistant assignments
# - 10 Availability slots per professor
# - FAQ items for each professor


async def seed_database():
    """Seed database with development data."""
    print("🌱 Starting database seeding...")
    
    # Create tables
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database seeding completed!")
    print(f"   - Tables created/verified")
    print(f"   - Ready for Phase 1 data population")


if __name__ == "__main__":
    asyncio.run(seed_database())
