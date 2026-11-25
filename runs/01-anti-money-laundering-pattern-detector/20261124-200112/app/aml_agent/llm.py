"""Simple LLM client wrapper. Uses OpenAI via environment if configured; otherwise a stub."""
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMS = int(os.environ.get("OPENAI_EMBEDDING_DIMS" , "1536"))
CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")


def _stub_llm(ftype, item):
    return {"type": ftype, "details": item, "narrative": f"[STUB] {ftype}: {item}"}


def get_llm_client():
    if OPENAI_API_KEY:
        try:
            from langchain import OpenAI
            # Return a simple callable that formats prompt and uses the LLM
            def call(ftype, item):
                prompt = f"Generate a short suspicious activity narrative for type={ftype} and details={item}"
                llm = OpenAI(openai_api_key=OPENAI_API_KEY, model_name=CHAT_MODEL)
                resp = llm(prompt)
                return {"type": ftype, "details": item, "narrative": resp}
            return call
        except Exception:
            return _stub_llm
    else:
        return _stub_llm
