import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "Vendor Performance Analytics"
    DATABASE_URL: str = (
        "mysql+pymysql://root:@localhost:3306/"
        "vendor_analytics_db?charset=utf8mb4"
    )
    SECRET_KEY: str = "dev-only-change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    DATASET_DIR: str = str(PROJECT_ROOT / "data")
    UPLOAD_DIR: str = str(BACKEND_DIR / "uploads_temp")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
        case_sensitive=True,
    )


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
