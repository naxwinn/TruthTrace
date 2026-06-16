from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    database_url: str = "sqlite:///./truthtrace.db"
    storage_dir: Path = Path("../storage")
    secret_key: str = "dev-secret-key-change-in-production"
    redis_url: str = "redis://localhost:6379/0"
    max_upload_size_mb: int = 500

    class Config:
        env_file = ".env"


settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
