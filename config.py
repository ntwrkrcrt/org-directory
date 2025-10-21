from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL
    DATABASE_URL: str
    DB_POOL_SIZE: int
    DB_ECHO: bool

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    REDIS_URL: str
    CACHE_TTL: int

    # API Security
    API_KEY: str

    # CORS Security
    allowed_origins: list[str] = [
        "http://localhost:8000",
    ]

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
