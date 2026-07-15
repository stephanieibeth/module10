from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = (
        "postgresql://postgres:postgres@db:5432/calculator_db"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()