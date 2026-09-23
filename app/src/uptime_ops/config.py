from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./uptime.db"
    check_interval_seconds: int = 30
    check_timeout_seconds: float = 5.0
    failure_threshold: int = 3
    discord_webhook_url: str = ""
    log_level: str = "INFO"


settings = Settings()
