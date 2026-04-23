"""
FastAPI application factory and main entry point.
Studentska Platforma za Univerzitetske Konsultacije
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging

from app.config import settings
from app.db.database import engine
from app.db.base import Base
from app.routes import appointments, availability, users, notifications, strikes, chat, files, auth, search, admin

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    Startup: Create database tables
    Shutdown: Clean up connections
    """
    # Startup
    logger.info("Starting FastAPI application...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Studentska Platforma API",
        description="Backend API za upravljanje univerzitetskim konsultacijama",
        version="1.0.0",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted Host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.fakultet.bg.ac.rs"]
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "environment": settings.environment}
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Studentska Platforma API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    
    # Include routers
    app.include_router(appointments.router)
    app.include_router(availability.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(notifications.router)
    app.include_router(strikes.router)
    app.include_router(chat.router)
    app.include_router(files.router)
    app.include_router(search.router)
    app.include_router(admin.router)
    
    logger.info("FastAPI application created successfully.")
    return app


# Create app instance with lifespan
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
