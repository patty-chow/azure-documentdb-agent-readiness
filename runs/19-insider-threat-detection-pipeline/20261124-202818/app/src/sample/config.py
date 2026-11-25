import os
from dotenv import load_dotenv

load_dotenv()

DOCUMENTDB_URI = os.environ.get("DOCUMENTDB_URI")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
ANOMALY_COSINE_THRESHOLD = float(os.environ.get("ANOMALY_COSINE_THRESHOLD", "0.7"))
DATABASE_NAME = os.environ.get("DATABASE_NAME", "sample_banking_19")
EMBEDDING_DIMS = 1536  # model-dependent; text-embedding-3-small assumed
