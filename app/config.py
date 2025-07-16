from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str
    api_key: str
    upload_directory: str = "uploads"
    max_file_size_mb: int = 10
    allowed_origins: List[str] = ["*"]  # Allow all origins for development, restrict in production

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()