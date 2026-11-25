import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# LangChain imports are optional at runtime; the agent will be used only if OPENAI_API_KEY is present
try:
    from langchain import PromptTemplate
    from langchain.chat_models import ChatOpenAI
    from langchain.schema import HumanMessage
except Exception:
    PromptTemplate = None
    ChatOpenAI = None


CARE_GAP_GUIDELINES = """
Care gap guidelines (examples):
- ColonCancer: Ages 50-75, colonoscopy within 10 years or FIT annually. If last_colonoscopy > 10 years or no record, flag.
- Mammogram: Females age 40-74, annual. If last_mammogram > 18 months or no record, flag.
- Diabetes-HbA1c: Patients with diagnosis code E11 (Type 2 Diabetes) should have an HbA1c within 12 months.

These guidelines are intentionally simplified for the sample.
"""


def prioritize_and_generate_talking_points(patients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """If OPENAI_API_KEY is present, call the LLM to prioritize and create talking points.
    Otherwise, create heuristic priorities and simple talking points locally.
    """
    if not OPENAI_API_KEY or ChatOpenAI is None:
        # Simple heuristic: older age and presence of a gap increases priority
        out = []
        for p in patients:
            priority = 1
            age = p.get("age", 0)
            if age >= 65:
                priority += 2
            if p.get("gap_types"):
                priority += len(p.get("gap_types"))
            talking_points = []
            for g in p.get("gap_types", []):
                if g == "ColonCancer":
                    talking_points.append("You are due for a colorectal cancer screening. We recommend scheduling a colonoscopy or stool-based test.")
                elif g == "Mammogram":
                    talking_points.append("You are due for a mammogram. Please contact the clinic to schedule your screening.")
                elif g == "Diabetes-HbA1c":
                    talking_points.append("We recommend an HbA1c test to monitor your diabetes control. Please schedule a lab appointment.")
            out.append({"patient_id": p.get("patient_id"), "priority": priority, "talking_points": talking_points})
        # sort by priority desc
        out.sort(key=lambda x: x["priority"], reverse=True)
        return out

    # Otherwise, call OpenAI via LangChain
    template = """
You are a clinical outreach coordinator. Given the following patients and their care gaps, produce a prioritized list and brief (2-3 sentence) outreach talking points for each patient. Prioritize by clinical risk (age, number of gaps, diagnosis severity). Output JSON array of objects: {patient_id, priority (1-10), talking_points: [..]}

Patients:
{patients_json}

Guidelines:
{guidelines}
"""
    prompt = PromptTemplate(template=template, input_variables=["patients_json", "guidelines"])
    model = ChatOpenAI(model=OPENAI_MODEL, openai_api_key=OPENAI_API_KEY, temperature=0.3)
    from json import dumps
    final_prompt = prompt.format(patients_json=dumps(patients), guidelines=CARE_GAP_GUIDELINES)
    resp = model.generate([HumanMessage(content=final_prompt)])
    # The real implementation should parse the model output as JSON; for brevity we return a placeholder
    return [{"patient_id": p.get("patient_id"), "priority": 5, "talking_points": ["(LLM output placeholder)"]} for p in patients]
