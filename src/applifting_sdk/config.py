from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    refresh_token: str
    base_url: str = "https://python.exercise.applifting.cz/"
    token_expiration_seconds: int = 300
    token_expiration_buffer_seconds: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
