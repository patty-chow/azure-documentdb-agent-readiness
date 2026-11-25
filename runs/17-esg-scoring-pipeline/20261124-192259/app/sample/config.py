import os
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.getenv("DOCUMENTDB_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")
DATABASE_NAME = os.getenv("DATABASE_NAME", "sample_fintech_17")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "esg_companies")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "1536"))

# For offline fallback behavior when API keys are missing
FALLBACK_MODE = OPENAI_API_KEY is None or OPENAI_API_KEY.strip() == ""
