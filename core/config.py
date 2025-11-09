from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str
    mongo_database_name: str
    telegram_token: str

    class Config:
        env_file = ".env"


settings = Settings()