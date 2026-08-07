import os
from typing import List, Union
from pydantic import AnyHttpUrl, Field, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "كود بالعربي"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    CSRF_SECRET: str = Field("default_csrf_secret_key_32_characters_long", env="CSRF_SECRET")
    
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000"
    ]
    
    COOKIE_DOMAIN: str = "localhost"
    SECURE_COOKIES: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./code_journey.db"
    SYNC_DATABASE_URL: str = "sqlite:///./code_journey.db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Code Execution
    JUDGE0_URL: str = "http://judge0:2358"
    JUDGE0_API_URL: str = "https://judge0-ce.p.rapidapi.com"
    JUDGE0_API_KEY: str = "mock_key"
    USE_MOCK_JUDGE0: bool = True
    ALLOW_LOCAL_RUNNER_IN_PROD: bool = False

    # Cloudflare Stream Video
    CLOUDFLARE_STREAM_ACCOUNT_ID: str = "mock_cf_account"
    CLOUDFLARE_STREAM_API_TOKEN: str = "mock_cf_token"
    CLOUDFLARE_STREAM_KEY_ID: str = "mock_cf_key_id"
    CLOUDFLARE_STREAM_PEM_KEY: str = "mock_cf_pem_key"
    USE_MOCK_VIDEO_PROVIDER: bool = True

    # Supabase Storage & Database
    SUPABASE_URL: Union[str, None] = None
    SUPABASE_SERVICE_ROLE_KEY: Union[str, None] = None
    SUPABASE_STORAGE_BUCKET: str = "payment-receipts"
    SIGNED_URL_SECRET: str = Field("default_signed_url_secret_32_characters_long", env="SIGNED_URL_SECRET")
    RUN_SEED: bool = False

    # Storage
    STORAGE_PROVIDER: str = "supabase"
    STORAGE_LOCAL_DIR: str = "./uploads"
    S3_ENDPOINT_URL: str = "https://mock.r2.cloudflarestorage.com"
    S3_ACCESS_KEY_ID: str = "mock_access_key"
    S3_SECRET_ACCESS_KEY: str = "mock_secret_key"
    S3_BUCKET_NAME: str = "code-journey-uploads"

    # App URLs
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000/api/v1"
    NEXT_PUBLIC_APP_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings(
    SECRET_KEY=os.getenv("SECRET_KEY", "dev_super_secret_key_change_in_production_32_chars_minimum!"),
    CSRF_SECRET=os.getenv("CSRF_SECRET", "csrf_super_secret_key_32_characters_at_least!")
)
