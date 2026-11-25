import os
from typing import Dict
from langchain.llms.base import LLM
from langchain.schema import LLMResult

# A deterministic stub LLM to avoid external API calls unless OPENAI_API_KEY is provided.
class StubLLM(LLM):
    def __init__(self, name: str = "stub"):
        self.name = name

    @property
    def _identifying_params(self) -> dict:
        return {"name": self.name}

    @property
    def _llm_type(self) -> str:
        return "stub"

    def _call(self, prompt: str, stop=None) -> str:
        # Very simple rule: if prompt mentions low credit score or <600 return 'reject'
        if "credit_score" in prompt:
            try:
                score = int(prompt.split("credit_score:")[-1].strip().split()[0])
                if score < 600:
                    return "reject"
                else:
                    return "approve"
            except Exception:
                return "approve"
        # default
        return "approve"

# Agent wrapper: underwriting and compliance
class UnderwritingAgent:
    def __init__(self, llm: LLM):
        self.llm = llm

    def decide(self, applicant: Dict) -> str:
        prompt = f"Evaluate applicant; credit_score: {applicant.get('credit_score', 700)}"
        return self.llm._call(prompt)

class ComplianceAgent:
    def __init__(self, llm: LLM):
        self.llm = llm

    def decide(self, applicant: Dict) -> str:
        # Simple deterministic rule via LLM prompt
        prompt = f"Check compliance for applicant name: {applicant.get('name')}"
        return self.llm._call(prompt)
