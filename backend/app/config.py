from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://knapresume:knapresume@127.0.0.1:5432/knapresume"
    session_ttl_hours: int = 12


settings = Settings()
