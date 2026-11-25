from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DOCUMENTDB_URI: str
    DATABASE_NAME: str = "sample_retail_15"

    class Config:
        env_file = ".env"


settings = Settings()
