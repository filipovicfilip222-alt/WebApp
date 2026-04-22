"""
Application configuration using Pydantic Settings.
All environment variables are type-safe and validated.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Studentska Platforma"
    environment: str = "development"
    log_level: str = "DEBUG"
    secret_key: str = "dev-secret-key-change-in-production"
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost/studentska_platforma"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""
    
    # Keycloak SSO
    keycloak_server_url: str = "http://localhost:8080"
    keycloak_realm: str = "fakultet"
    keycloak_client_id: str = "fakultet-backend"
    keycloak_client_secret: str = "change-me"
    skip_jwt_validation: bool = True
    
    # MinIO Object Storage
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "appointment-files"
    minio_secure: bool = False  # Use HTTP in dev, HTTPS in prod
    
    # Google Programmable Search Engine
    google_pse_api_key: str = ""
    google_pse_cx: str = ""
    
    # SMTP Email Configuration
    smtp_server: str = "localhost"
    smtp_port: int = 25
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@fakultet.bg.ac.rs"
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # CORS Configuration
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]
    
    # Rate Limiting
    rate_limit_appointments_per_minute: int = 5  # Per user
    rate_limit_api_per_minute: int = 100  # Per IP
    
    # Appointment Settings
    slot_lock_ttl_seconds: int = 30  # Redis lock duration
    slot_booking_buffer_minutes: int = 5  # Minutes between appointments
    appointment_max_files_mb: int = 5
    appointment_max_files_per_appointment: int = 5
    
    # Strike System
    strike_block_threshold: int = 3  # Strikes before blocking
    strike_block_duration_days: int = 14
    strike_expiry_days: int = 90
    no_show_detection_minutes: int = 30  # After appointment time
    
    # Notification Settings
    notification_email_delay_seconds: int = 5
    notification_max_broadcast_delay_seconds: int = 300
    
    # Waitlist Settings
    waitlist_offer_duration_hours: int = 2
    
    # Chat Settings
    ticket_chat_max_messages: int = 20
    ticket_chat_auto_close_hours: int = 24
    
    # Time Zone
    timezone: str = "Europe/Belgrade"
    
    # Feature Flags (for A/B testing)
    enable_web_push: bool = False
    enable_ai_search: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Convert env var names like DATABASE_URL to database_url
        populate_by_name = True
    
    @property
    def database_url_sync(self) -> str:
        """Synchronous database URL for Alembic migrations."""
        return self.database_url.replace("+asyncpg", "")
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"


# Global settings instance
settings = Settings()
