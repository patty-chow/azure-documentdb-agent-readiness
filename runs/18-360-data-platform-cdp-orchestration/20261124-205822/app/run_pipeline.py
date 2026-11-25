import argparse
import os
from dotenv import load_dotenv
from src.db import get_database
from src.pipeline import Orchestrator
from src.utils import deterministic_embedding

load_dotenv()

# Minimal embedding fn: use OpenAI via langchain if available, else deterministic
OPENAI_KEY = os.getenv("OPENAI_API_KEY")


def embeddings_fn(texts):
    # Accepts a single string or list
    if not OPENAI_KEY:
        # return deterministic small embedding for demo
        if isinstance(texts, str):
            return deterministic_embedding(texts, dims=8)
        return [deterministic_embedding(t, dims=8) for t in texts]
    try:
        from langchain.embeddings import OpenAIEmbeddings
        emb = OpenAIEmbeddings()
        if isinstance(texts, str):
            return emb.embed_query(texts)
        return emb.embed_documents(texts)
    except Exception:
        if isinstance(texts, str):
            return deterministic_embedding(texts, dims=8)
        return [deterministic_embedding(t, dims=8) for t in texts]


def llm_fn(group):
    # Ask a chat model whether to merge; return a dict with canonical doc and remove_ids
    if not OPENAI_KEY:
        return None
    try:
        from langchain.chat_models import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage
        llm = ChatOpenAI(temperature=0)
        prompt = "Decide whether the following customer documents represent the same person. If yes, return a JSON object with a 'canonical' document and a 'remove_ids' array of ids to delete. If no, return {}. Documents: " + str(group)
        resp = llm([SystemMessage(content="You are a data engineer."), HumanMessage(content=prompt)])
        text = resp.content
        import json
        return json.loads(text)
    except Exception:
        return None


def main(args):
    db = get_database()
    orchestrator = Orchestrator(db, embeddings_fn=embeddings_fn, llm_fn=llm_fn)
    if args.seed:
        # run seed script
        import seed
        seed.seed()
    if args.run:
        print("Running pipeline (ingest/dedupe/enrich) ...")
        res = orchestrator.run_batch()
        print("Workflow record:", res)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument("--seed", action="store_true", help="Run the seed script first")
    p.add_argument("--run", action="store_true", help="Run the pipeline")
    args = p.parse_args()
    main(args)
