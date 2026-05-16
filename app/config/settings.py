from functools import cached_property
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str | None = None
    refresh_secret_key: str | None = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    environment: str = "development"
    frontend_url: str = "http://localhost:3000"
    cors_allowed_origins: str = ""
    onlyoffice_url: str = "http://localhost:8080"
    browser_backend_url: str = "http://localhost:8000"
    public_backend_url: str = "http://host.docker.internal:8000"
    storage_backend: str = "local"
    storage_local_dir: Path = Path("storage/documents")
    storage_bucket: str | None = None
    storage_region: str | None = None
    storage_endpoint_url: str | None = None
    storage_access_key_id: str | None = None
    storage_secret_access_key: str | None = None
    storage_addressing_style: str = "path"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @cached_property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @cached_property
    def cors_origins(self) -> list[str]:
        configured_origins = [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]
        origins = list(dict.fromkeys([self.frontend_url, *configured_origins]))
        if self.is_production and "*" in origins:
            raise ValueError("CORS wildcard is not allowed in production")
        return origins

    def require_secret_key(self) -> str:
        if not self.secret_key:
            raise RuntimeError("SECRET_KEY environment variable is required")
        return self.secret_key

    def require_refresh_secret_key(self) -> str:
        if not self.refresh_secret_key:
            raise RuntimeError("REFRESH_SECRET_KEY environment variable is required")
        return self.refresh_secret_key

    def public_url(self, path: str) -> str:
        return f"{self.public_backend_url.rstrip('/')}{path}"

    def browser_url(self, path: str) -> str:
        return f"{self.browser_backend_url.rstrip('/')}{path}"


settings = Settings()
