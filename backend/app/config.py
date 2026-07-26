from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_SECRET = "change-me-in-production-use-openssl-rand-hex-32"


def normalize_database_url(url: str) -> str:
    """Railway and other hosts may provide postgres:// — SQLAlchemy needs postgresql://."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(default="development", alias="ENVIRONMENT")

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="AI_NEMO_DB", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="", alias="POSTGRES_PASSWORD")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(
        default=8000,
        validation_alias=AliasChoices("PORT", "API_PORT"),
    )
    cors_origins: str = Field(
        default="http://localhost:3000",
        alias="CORS_ORIGINS",
    )
    cors_origin_regex: str | None = Field(
        default=None,
        alias="CORS_ORIGIN_REGEX",
    )
    jwt_secret_key: str = Field(
        default=_DEFAULT_JWT_SECRET,
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60, alias="JWT_EXPIRE_MINUTES")
    jwt_refresh_expire_days: int = Field(default=7, alias="JWT_REFRESH_EXPIRE_DAYS")
    demo_user_email: str = Field(
        default="auditor@demo.auditai.com", alias="DEMO_USER_EMAIL"
    )
    demo_user_password: str = Field(default="AuditAI2026!", alias="DEMO_USER_PASSWORD")
    max_upload_mb: int = Field(default=10, alias="MAX_UPLOAD_MB")
    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")
    s3_bucket: str | None = Field(
        default=None,
        validation_alias=AliasChoices("S3_BUCKET", "STORAGE_S3_BUCKET"),
    )
    s3_region: str | None = Field(
        default=None,
        validation_alias=AliasChoices("S3_REGION", "AWS_REGION", "AWS_DEFAULT_REGION"),
    )
    s3_endpoint_url: str | None = Field(default=None, alias="S3_ENDPOINT_URL")
    s3_access_key_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("S3_ACCESS_KEY_ID", "AWS_ACCESS_KEY_ID"),
    )
    s3_secret_access_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("S3_SECRET_ACCESS_KEY", "AWS_SECRET_ACCESS_KEY"),
    )
    frontend_url: str = Field(
        default="http://localhost:3000",
        alias="FRONTEND_URL",
    )
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str = Field(
        default="AuditAI Platform <noreply@auditai.com>",
        alias="SMTP_FROM",
    )
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    invite_token_expire_days: int = Field(default=7, alias="INVITE_TOKEN_EXPIRE_DAYS")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod")

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return normalize_database_url(self.database_url)
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def uses_default_jwt_secret(self) -> bool:
        return self.jwt_secret_key == _DEFAULT_JWT_SECRET

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_from)


@lru_cache
def get_settings() -> Settings:
    return Settings()
