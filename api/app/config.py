from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    http_user_agent: str
    nav_feed_base_url: str
    nav_feed_token: str


settings = Settings()
