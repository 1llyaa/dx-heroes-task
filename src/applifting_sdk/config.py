
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    refresh_token: str | None = None
    base_url: str = "https://python.exercise.applifting.cz/"
    token_expiration_seconds: int = 300
    token_expiration_buffer_seconds: int = 5

    class Config:
        env_file: str = ".env"
        env_file_encoding: str = "utf-8"


settings: Settings = Settings()
