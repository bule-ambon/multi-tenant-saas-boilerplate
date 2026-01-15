"""
Application Configuration Management
Handles all environment variables and application settings
"""
import secrets
import json
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, EmailStr, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "Multi-Tenant SaaS Platform"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    DEBUG: bool = True
    AUTO_INIT_DB: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        return cls._parse_list_input(v)

    @field_validator("QBO_SCOPES", mode="before")
    @classmethod
    def assemble_qbo_scopes(cls, v: Union[str, List[str]]) -> List[str]:
        return cls._parse_list_input(v)

    @staticmethod
    def _parse_list_input(v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("["):
                return json.loads(v)
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        raise ValueError(v)

    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_PRE_PING: bool = True

    # Multi-Tenancy
    TENANCY_MODE: str = "shared"  # shared or isolated
    TENANT_IDENTIFICATION: str = "subdomain"  # subdomain or header
    TENANT_HEADER_NAME: str = "X-Tenant-ID"
    DEFAULT_TENANT_DB_PREFIX: str = "tenant_"

    # Authentication
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    REQUIRE_EMAIL_VERIFICATION: bool = True
    REQUIRE_MFA_FOR_ADMIN: bool = False
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30

    # OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_REDIRECT_URI: Optional[str] = None

    # QuickBooks Online OAuth
    QBO_CLIENT_ID: Optional[str] = None
    QBO_CLIENT_SECRET: Optional[str] = None
    QBO_REDIRECT_URI: Optional[str] = None
    QBO_SCOPES: List[str] = ["com.intuit.quickbooks.accounting"]
    QBO_AUTHORIZATION_URL: str = "https://appcenter.intuit.com/connect/oauth2"
    QBO_TOKEN_URL: str = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    QBO_API_BASE_URL: str = "https://quickbooks.api.intuit.com"

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_API_VERSION: str = "2023-10-16"

    # Paystack (Alternative)
    PAYSTACK_SECRET_KEY: Optional[str] = None
    PAYSTACK_PUBLIC_KEY: Optional[str] = None

    # Flutterwave (Alternative)
    FLUTTERWAVE_SECRET_KEY: Optional[str] = None
    FLUTTERWAVE_PUBLIC_KEY: Optional[str] = None

    # Redis
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL: int = 3600
    SESSION_TTL: int = 86400

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    FROM_EMAIL: EmailStr = "noreply@yoursaas.com"
    FROM_NAME: str = "Multi-Tenant SaaS Platform"

    # File Storage
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB

    # Security
    CORS_ORIGINS: str = "http://localhost:3000"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    ENABLE_CSRF_PROTECTION: bool = True
    CSRF_SECRET_KEY: str = secrets.token_urlsafe(32)
    ENCRYPTION_KEY: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_STRATEGY: str = "sliding-window"
    RATE_LIMIT_STORAGE: str = "redis"

    # Monitoring
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    ENABLE_SQL_LOGGING: bool = False
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = True

    # Feature Flags
    ENABLE_OAUTH: bool = True
    ENABLE_MFA: bool = True
    ENABLE_WEBHOOKS: bool = True
    ENABLE_AUDIT_LOGS: bool = True
    ENABLE_USAGE_TRACKING: bool = True

    # Billing
    DEFAULT_TRIAL_DAYS: int = 14
    ENABLE_PRORATION: bool = True
    INVOICE_AUTO_SEND: bool = True
    BILLING_CURRENCY: str = "USD"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Frontend URLs
    FRONTEND_URL: AnyHttpUrl = "http://localhost:3000"
    VERIFY_EMAIL_URL: str = "http://localhost:3000/verify-email"
    RESET_PASSWORD_URL: str = "http://localhost:3000/reset-password"

    # Admin
    SUPER_ADMIN_EMAIL: EmailStr = "admin@yoursaas.com"
    SUPER_ADMIN_PASSWORD: str = "ChangeThisPassword123!"

    # Deployment
    WORKERS_PER_CORE: int = 1
    MAX_WORKERS: int = 4
    KEEP_ALIVE: int = 5

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL"""
        return str(self.DATABASE_URL).replace("+asyncpg", "")

    @property
    def database_url_async(self) -> str:
        """Get asynchronous database URL"""
        url = str(self.DATABASE_URL)
        if "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        return url

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def qbo_scope_string(self) -> str:
        """QuickBooks OAuth scopes as a single string"""
        return " ".join(self.QBO_SCOPES)


# Global settings instance
settings = Settings()
