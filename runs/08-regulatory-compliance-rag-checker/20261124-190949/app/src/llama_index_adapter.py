"""
Adapter example: how to build a LlamaIndex (GPTVectorStoreIndex) from documents
retrieved from DocumentDB. This file is an example only — the runtime sample uses
OpenAI calls directly for simplicity and reliability.

To use LlamaIndex as the runtime engine, builders can import these helpers and
replace call_llm/build_prompt with a LlamaIndex query flow.
"""
from llama_index import Document, GPTVectorStoreIndex, LLMPredictor, ServiceContext
from llama_index.llms import OpenAI


def build_llama_index_from_docs(docs, openai_api_key, llm_model="gpt-3.5-turbo"):
    # docs: list of dicts with 'content' and metadata
    documents = [Document(text=d.get("content",""), doc_id=d.get("_id"), extra_info={"title": d.get("title")}) for d in docs]
    llm = OpenAI(api_key=openai_api_key, model=llm_model)
    llm_predictor = LLMPredictor(llm=llm)
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)
    index = GPTVectorStoreIndex.from_documents(documents, service_context=service_context)
    return index
