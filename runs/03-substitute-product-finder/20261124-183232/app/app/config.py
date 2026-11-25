from pydantic import BaseSettings, Field, ValidationError


class Settings(BaseSettings):
    """Application configuration read from environment or a .env file.

    DOCUMENTDB_URI: MongoDB connection string for Azure DocumentDB. Required.
    OPENAI_API_KEY: Optional OpenAI API key; when missing the ingest script will fall back to deterministic vectors.
    DB_NAME: Database name to use for this sample (default: sample_retail_03).
    """

    DOCUMENTDB_URI: str = Field(..., env="DOCUMENTDB_URI")
    OPENAI_API_KEY: str | None = Field(None, env="OPENAI_API_KEY")
    DB_NAME: str = Field("sample_retail_03", env="DB_NAME")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Load settings and provide clear errors if not present.
try:
    settings = Settings()
except ValidationError as e:
    # Raise a clear, developer-friendly error explaining what's missing.
    raise RuntimeError(
        "Missing required environment configuration. Please copy .env.example to .env and set DOCUMENTDB_URI.\n"
        + str(e)
    )
