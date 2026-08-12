import json
import os
from ipaddress import ip_network
from typing import List, Optional
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_list_env(value: object, default: List[str]) -> List[str]:
    if value is None or value == "":
        return default
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        if text.startswith("["):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in text.split(",") if item.strip()]
    return default


def _default_local_frontend_origins() -> List[str]:
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


def _default_trusted_proxy_ips() -> List[str]:
    return ["127.0.0.1", "::1"]


def _default_trusted_proxy_cidrs() -> List[str]:
    return ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "كود بالعربي"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    CSRF_SECRET: str = Field("default_csrf_secret_key_32_characters_long", env="CSRF_SECRET")
    SIGNED_URL_SECRET: str = Field("default_signed_url_secret_32_characters_long", env="SIGNED_URL_SECRET")
    RECEIPT_SIGNING_SECRET: str = Field("default_receipt_signing_secret_32_characters_long", env="RECEIPT_SIGNING_SECRET")
    VIDEO_SIGNING_SECRET: str = Field("default_video_signing_secret_32_characters_long", env="VIDEO_SIGNING_SECRET")

    ALLOWED_ORIGINS: List[str] = Field(default_factory=_default_local_frontend_origins)
    CSRF_TRUSTED_ORIGINS: List[str] = Field(default_factory=_default_local_frontend_origins)
    TRUSTED_PROXY_IPS: List[str] = Field(default_factory=_default_trusted_proxy_ips)
    TRUSTED_PROXY_CIDRS: List[str] = Field(default_factory=_default_trusted_proxy_cidrs)

    COOKIE_DOMAIN: str = "localhost"
    COOKIE_SAMESITE: str = "lax"
    SECURE_COOKIES: bool = False

    DATABASE_URL: str = "sqlite+aiosqlite:///./code_journey.db"
    SYNC_DATABASE_URL: str = "sqlite:///./code_journey.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 10

    REDIS_URL: str = "redis://localhost:6379/0"

    JUDGE0_URL: Optional[str] = "http://judge0:2358"
    JUDGE0_API_URL: Optional[str] = None
    JUDGE0_API_KEY: Optional[str] = None
    USE_MOCK_JUDGE0: bool = False
    ALLOW_UNSAFE_LOCAL_CODE_EXECUTION: bool = True
    ALLOW_LOCAL_RUNNER_IN_PROD: bool = False

    CLOUDFLARE_STREAM_ACCOUNT_ID: Optional[str] = "mock_cf_account"
    CLOUDFLARE_STREAM_API_TOKEN: Optional[str] = "mock_cf_token"
    CLOUDFLARE_STREAM_KEY_ID: Optional[str] = "mock_cf_key_id"
    CLOUDFLARE_STREAM_PEM_KEY: Optional[str] = "mock_cf_pem_key"
    CLOUDFLARE_STREAM_CUSTOMER_SUBDOMAIN: Optional[str] = "mock_cf_customer"
    BUNNY_STREAM_LIBRARY_ID: Optional[str] = "mock_bunny_lib_id"
    BUNNY_STREAM_API_KEY: Optional[str] = "mock_bunny_api_key"
    BUNNY_STREAM_TOKEN_AUTH_KEY: Optional[str] = "mock_bunny_token_key"
    USE_MOCK_VIDEO_PROVIDER: bool = True

    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_STORAGE_BUCKET: str = "payment-receipts"
    RUN_SEED: bool = False

    STORAGE_PROVIDER: str = "supabase"
    STORAGE_LOCAL_DIR: str = "./storage_uploads"
    PRIVATE_STORAGE_LOCAL_DIR: str = "./private_storage"
    PUBLIC_ASSETS_LOCAL_DIR: str = "./public_assets"
    S3_ENDPOINT_URL: Optional[str] = "https://mock.r2.cloudflarestorage.com"
    S3_ACCESS_KEY_ID: Optional[str] = "mock_access_key"
    S3_SECRET_ACCESS_KEY: Optional[str] = "mock_secret_key"
    S3_BUCKET_NAME: Optional[str] = "code-journey-uploads"

    NEXT_PUBLIC_API_URL: str = "http://localhost:8000/api/v1"
    NEXT_PUBLIC_APP_URL: str = "http://localhost:3000"
    PASSWORD_RESET_DELIVERY_PROVIDER: str = "mock"
    PASSWORD_RESET_SMTP_HOST: Optional[str] = None
    PASSWORD_RESET_SMTP_PORT: int = 587
    PASSWORD_RESET_SMTP_USERNAME: Optional[str] = None
    PASSWORD_RESET_SMTP_PASSWORD: Optional[str] = None
    PASSWORD_RESET_SMTP_FROM: Optional[str] = None
    PASSWORD_RESET_SMS_WEBHOOK_URL: Optional[str] = None
    PASSWORD_RESET_SMS_WEBHOOK_TOKEN: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def ensure_async_db_url(cls, value: object) -> str:
        db_url = str(value or os.getenv("DATABASE_URL") or "sqlite+aiosqlite:///./code_journey.db")
        if db_url.startswith("postgresql://"):
            return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return db_url

    @field_validator("SYNC_DATABASE_URL", mode="before")
    @classmethod
    def set_sync_db_url(cls, value: object) -> str:
        configured = value or os.getenv("SYNC_DATABASE_URL") or os.getenv("DATABASE_URL")
        db_url = str(configured or "sqlite:///./code_journey.db")
        if db_url.startswith("postgresql+asyncpg://"):
            return db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        if db_url.startswith("sqlite+aiosqlite://"):
            return db_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        return db_url

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> List[str]:
        return _parse_list_env(value, _default_local_frontend_origins())

    @field_validator("CSRF_TRUSTED_ORIGINS", mode="before")
    @classmethod
    def parse_csrf_trusted_origins(cls, value: object) -> List[str]:
        return _parse_list_env(value, _default_local_frontend_origins())

    @field_validator("TRUSTED_PROXY_IPS", mode="before")
    @classmethod
    def parse_trusted_proxy_ips(cls, value: object) -> List[str]:
        return _parse_list_env(value, _default_trusted_proxy_ips())

    @field_validator("TRUSTED_PROXY_CIDRS", mode="before")
    @classmethod
    def parse_trusted_proxy_cidrs(cls, value: object) -> List[str]:
        return _parse_list_env(value, _default_trusted_proxy_cidrs())

    @field_validator("COOKIE_SAMESITE")
    @classmethod
    def validate_cookie_samesite(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("COOKIE_SAMESITE must be one of: lax, strict, none")
        return normalized

    @field_validator("PASSWORD_RESET_DELIVERY_PROVIDER")
    @classmethod
    def validate_password_reset_delivery_provider(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in {"mock", "disabled", "smtp_email", "sms_webhook"}:
            raise ValueError(
                "PASSWORD_RESET_DELIVERY_PROVIDER must be one of: mock, disabled, smtp_email, sms_webhook"
            )
        return normalized

    def is_development_like(self) -> bool:
        return self.ENVIRONMENT in {"development", "test"}

    def requires_isolated_code_execution(self) -> bool:
        return self.ENVIRONMENT in {"staging", "production"}

    def is_mock_value(self, value: Optional[str]) -> bool:
        if value is None:
            return True
        lowered = value.strip().lower()
        return lowered == "" or any(marker in lowered for marker in ("mock", "default_", "change_in_production"))

    def is_password_reset_delivery_configured(self) -> bool:
        provider = self.PASSWORD_RESET_DELIVERY_PROVIDER
        if provider == "mock":
            return self.is_development_like()
        if provider == "disabled":
            return False
        if provider == "smtp_email":
            return all(
                [
                    self.PASSWORD_RESET_SMTP_HOST,
                    self.PASSWORD_RESET_SMTP_USERNAME,
                    self.PASSWORD_RESET_SMTP_PASSWORD,
                    self.PASSWORD_RESET_SMTP_FROM,
                ]
            )
        if provider == "sms_webhook":
            return bool(self.PASSWORD_RESET_SMS_WEBHOOK_URL)
        return False

    def is_video_provider_configured(self, provider: str) -> bool:
        normalized = (provider or "").lower()
        if normalized == "local":
            return self.is_development_like() and self.USE_MOCK_VIDEO_PROVIDER
        if normalized == "cloudflare_stream":
            return all(
                [
                    self.CLOUDFLARE_STREAM_ACCOUNT_ID and not self.is_mock_value(self.CLOUDFLARE_STREAM_ACCOUNT_ID),
                    self.CLOUDFLARE_STREAM_CUSTOMER_SUBDOMAIN
                    and not self.is_mock_value(self.CLOUDFLARE_STREAM_CUSTOMER_SUBDOMAIN),
                    (
                        self.CLOUDFLARE_STREAM_API_TOKEN and not self.is_mock_value(self.CLOUDFLARE_STREAM_API_TOKEN)
                    )
                    or (
                        self.CLOUDFLARE_STREAM_KEY_ID
                        and not self.is_mock_value(self.CLOUDFLARE_STREAM_KEY_ID)
                        and self.CLOUDFLARE_STREAM_PEM_KEY
                        and not self.is_mock_value(self.CLOUDFLARE_STREAM_PEM_KEY)
                    ),
                ]
            )
        if normalized == "bunny_stream":
            return all(
                [
                    self.BUNNY_STREAM_LIBRARY_ID and not self.is_mock_value(self.BUNNY_STREAM_LIBRARY_ID),
                    self.BUNNY_STREAM_TOKEN_AUTH_KEY and not self.is_mock_value(self.BUNNY_STREAM_TOKEN_AUTH_KEY),
                ]
            )
        return False

    def normalize_origin(self, origin: str) -> Optional[tuple[str, str, int]]:
        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return None
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return parsed.scheme, parsed.hostname.lower(), port

    def is_csrf_origin_trusted(self, origin: str) -> bool:
        normalized_origin = self.normalize_origin(origin)
        if normalized_origin is None:
            return False
        origin_scheme, origin_host, origin_port = normalized_origin
        for configured_origin in self.CSRF_TRUSTED_ORIGINS:
            normalized_config = self.normalize_origin(configured_origin)
            if normalized_config is None:
                continue
            trusted_scheme, trusted_host, trusted_port = normalized_config
            if trusted_scheme != origin_scheme or trusted_port != origin_port:
                continue
            if trusted_host.startswith("."):
                boundary_host = trusted_host[1:]
                if origin_host == boundary_host or origin_host.endswith(f".{boundary_host}"):
                    return True
            elif origin_host == trusted_host:
                return True
        return False

    def trusted_proxy_networks(self) -> list:
        networks = []
        for cidr in self.TRUSTED_PROXY_CIDRS:
            try:
                networks.append(ip_network(cidr, strict=False))
            except ValueError:
                continue
        return networks


settings = Settings(
    SECRET_KEY=os.getenv("SECRET_KEY", "dev_super_secret_key_change_in_production_32_chars_minimum!"),
    CSRF_SECRET=os.getenv("CSRF_SECRET", "csrf_super_secret_key_32_characters_at_least!"),
    SIGNED_URL_SECRET=os.getenv("SIGNED_URL_SECRET", "signed_url_super_secret_key_32_characters_at_least!"),
    RECEIPT_SIGNING_SECRET=os.getenv("RECEIPT_SIGNING_SECRET", "receipt_signing_secret_32_characters_at_least!"),
    VIDEO_SIGNING_SECRET=os.getenv("VIDEO_SIGNING_SECRET", "video_signing_secret_32_characters_at_least!"),
)

if settings.requires_isolated_code_execution():
    if settings.ALLOW_UNSAFE_LOCAL_CODE_EXECUTION or settings.ALLOW_LOCAL_RUNNER_IN_PROD:
        raise RuntimeError(
            "FATAL: unsafe local code execution must remain disabled in staging and production."
        )
    if settings.USE_MOCK_VIDEO_PROVIDER:
        raise RuntimeError(
            "FATAL: mock video playback must remain disabled in staging and production."
        )

# Production/staging secrets must never use repo defaults or mock placeholders.
if not settings.is_development_like():
    bad_markers = ("dev_", "mock", "change_in_production", "default_")
    for name, value in [
        ("SECRET_KEY", settings.SECRET_KEY),
        ("CSRF_SECRET", settings.CSRF_SECRET),
        ("SIGNED_URL_SECRET", settings.SIGNED_URL_SECRET),
        ("RECEIPT_SIGNING_SECRET", settings.RECEIPT_SIGNING_SECRET),
        ("VIDEO_SIGNING_SECRET", settings.VIDEO_SIGNING_SECRET),
    ]:
        lowered = value.lower()
        if any(marker in lowered for marker in bad_markers):
            raise RuntimeError(
                f"FATAL: {name} contains a default or mock value. "
                f"Set a strong unique secret before running in {settings.ENVIRONMENT}."
            )
