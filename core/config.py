from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://admin:dfghdfjkghdfkjghdfkjgh@138.124.49.112:27017/?authSource=admin"

    class Config:
        env_file = ".env"


settings = Settings()