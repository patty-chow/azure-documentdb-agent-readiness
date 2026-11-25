import os
from typing import Any
from dotenv import load_dotenv
from langchain import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from .agents import GPAgent, SpecialistAgent, PharmacyAgent
from .db import make_care_plan_doc, insert_care_plan

load_dotenv()

LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

# Simple orchestrator that queries three agents and synthesises a care plan via an LLM
class Orchestrator:
    def __init__(self):
        self.gp = GPAgent()
        self.spec = SpecialistAgent()
        self.pharm = PharmacyAgent()
        # LangChain LLM wrapper — configure with OPENAI_API_KEY via env at init time
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        # If OPENAI_API_KEY is missing, LangChain will raise; tests can set the env var or mock LLMChain
        self.llm = OpenAI(model_name=LLM_MODEL, openai_api_key=openai_api_key)

    def synthesize_plan(self, gp_notes: str, referrals: str, meds: list) -> str:
        prompt = PromptTemplate(
            input_variables=["gp_notes", "referrals", "meds"],
            template=(
                "You are a clinical care-planning assistant. Given the patient's primary care notes, referral notes, "
                "and current medication list, synthesise a clear, concise unified care plan with tasks, responsible parties, "
                "and follow-up timeline.\n\nPRIMARY CARE NOTES:\n{gp_notes}\n\nREFERRALS:\n{referrals}\n\nMEDICATIONS:\n{meds}\n\nOUTPUT: Produce a care plan in plain text."
            ),
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.run({"gp_notes": gp_notes, "referrals": referrals, "meds": ", ".join(meds)})
        return result

    def orchestrate(self, patient_id: str) -> Any:
        gp = self.gp.fetch(patient_id)
        spec = self.spec.fetch(patient_id)
        pharm = self.pharm.fetch(patient_id)

        plan_text = self.synthesize_plan(gp.get("notes", ""), spec.get("referrals", ""), pharm.get("medications", []))

        doc = make_care_plan_doc(patient_id, plan_text, sources=[
            {"agent": "gp", "count": len(gp.get("records", []))},
            {"agent": "specialist", "count": len(spec.get("records", []))},
            {"agent": "pharmacy", "count": len(pharm.get("records", []))},
        ])
        inserted_id = insert_care_plan(doc)
        return {"inserted_id": str(inserted_id), "plan_text": plan_text}
