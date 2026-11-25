import os
from typing import Any, Dict, List
from langchain import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

# Small wrappers around an LLM to produce human-friendly text for validation and filing

MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        if OPENAI_API_KEY:
            _llm = ChatOpenAI(model_name=MODEL_NAME, temperature=0.2)
        else:
            _llm = None
    return _llm


def validation_summary(rule_results: Dict[str, Any], sample_records: List[Dict[str, Any]]) -> str:
    """Return a human-friendly validation summary. If an LLM key is available use it, otherwise build a deterministic summary."""
    llm = get_llm()
    summary_text = []
    for rule, result in rule_results.items():
        summary_text.append(f"Rule: {rule} => {result}")

    if llm is None:
        # deterministic fallback
        return "\n".join(summary_text)

    prompt = PromptTemplate(
        input_variables=["rules", "examples"],
        template=("You are a compliance assistant. Summarize the validation results:\n\nRules:\n{rules}\n\n" 
                  "Provide a short bullet summary and suggest next steps if any failures are present. "
                  "Include up to 3 example records from the examples JSON."),
    )
    rendered = prompt.format(rules="\n".join(summary_text), examples=str(sample_records[:3]))
    resp = llm([HumanMessage(content=rendered)])
    return resp.content


def format_filing(reporting_period: str, extracted: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
    """Produce a filing JSON structure. Use LLM if available for human-readable narrative."""
    llm = get_llm()
    filing = {
        "reporting_period": reporting_period,
        "records_count": sum(len(v) for v in extracted.values()),
        "extracted": extracted,
        "validation": validation,
    }

    if llm is None:
        filing["narrative"] = "Filing generated without LLM. See validation and extracted sections."
        return filing

    # Ask LLM to produce a short narrative
    prompt = PromptTemplate(
        input_variables=["period", "counts", "validation_summary"],
        template=("Produce a concise filing narrative for period {period}. Counts: {counts}. "
                  "Validation summary: {validation_summary}. Keep under 120 words."),
    )
    rendered = prompt.format(period=reporting_period, counts=str({k: len(v) for k,v in extracted.items()}), validation_summary=str(validation))
    resp = llm([HumanMessage(content=rendered)])
    filing["narrative"] = resp.content
    return filing
