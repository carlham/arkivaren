from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    http_user_agent: str
    min_request_interval_seconds: float = 10.0


settings = Settings()
