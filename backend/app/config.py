import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Inspection and Risk Prevention System"
    VERSION: str = "1.0.0 - Phase 1 MVP"
    API_PREFIX: str = "/api/v1"
    
    # Defaults to local SQLite for zero-config startup; seamlessly connects to PostgreSQL when DATABASE_URL is set
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./smart_inspection.db")
    
    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "smart-inspection-super-secret-key-capstone-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Evidence Upload Directory
    UPLOAD_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))

    class Config:
        env_file = ".env"

settings = Settings()

# Ensure uploads directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
