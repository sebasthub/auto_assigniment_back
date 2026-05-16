from functools import cached_property

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


settings = Settings()
