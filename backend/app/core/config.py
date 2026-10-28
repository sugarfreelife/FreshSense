from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )

    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    DATABASE_URL: str = "sqlite:///./freshsense-demo.db"
    JWT_SECRET: str = Field(min_length=32)
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, gt=0)
    MODEL_PATH: str = "./models"
    PRODUCT_RECOGNITION_ENABLED: bool = True
    UPLOAD_DIR: str = "./uploads"
    OCR_PROVIDER: str = "local"
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        url = value.strip()
        if url.startswith("postgres://"):
            url = "postgresql+psycopg2://" + url[len("postgres://") :]
        if not url.startswith(("postgresql://", "postgresql+psycopg2://", "sqlite:///")):
            raise ValueError("DATABASE_URL must be a PostgreSQL or SQLite connection URL")
        return url

    @property
    def sqlalchemy_url(self) -> str:
        return self.DATABASE_URL

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.ENVIRONMENT == "production":
            if not self.DATABASE_URL.startswith(("postgresql://", "postgresql+psycopg2://")):
                raise ValueError("Production requires PostgreSQL; SQLite is for local demos only.")
            if not self.cors_origins_list:
                raise ValueError("Production must configure at least one exact HTTPS CORS origin.")
            for origin in self.cors_origins_list:
                parsed = urlsplit(origin)
                if (
                    parsed.scheme != "https"
                    or not parsed.hostname
                    or parsed.username
                    or parsed.password
                    or parsed.path not in ("", "/")
                    or parsed.query
                    or parsed.fragment
                    or "*" in origin
                ):
                    raise ValueError("Each production CORS origin must be one exact HTTPS origin without a path or wildcard.")
            if self.JWT_SECRET.strip().lower().startswith(("replace-with", "change-me", "your-secret")):
                raise ValueError("Replace the example JWT secret before using production settings.")
        return self


settings = Settings()
