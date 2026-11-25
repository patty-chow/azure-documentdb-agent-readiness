import os
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

from db import get_db
from agent import prioritize_and_generate_talking_points

load_dotenv()

DB = get_db()


def compute_age(dob):
    if not dob:
        return None
    today = datetime.utcnow().date()
    try:
        birthday = dob.date()
    except Exception:
        birthday = dob
    years = relativedelta(today, birthday).years
    return years


def find_care_gaps(limit=1000):
    # Aggregate patients with their most recent visit
    pipeline = [
        {"$lookup": {
            "from": "visits",
            "localField": "patient_id",
            "foreignField": "patient_id",
            "as": "visits"
        }},
        {"$addFields": {
            "last_visit": {"$max": "$visits.visit_date"}
        }},
        {"$project": {
            "patient_id": 1,
            "dob": 1,
            "gender": 1,
            "diagnosis_codes": 1,
            "last_visit": 1,
            "contact": 1
        }},
        {"$limit": limit}
    ]

    docs = list(DB.patients.aggregate(pipeline))

    flagged = []
    for d in docs:
        dob = d.get("dob")
        age = compute_age(dob)
        last_visit = d.get("last_visit")
        diag = d.get("diagnosis_codes", []) or []
        gaps = []
        # Colon cancer guideline (simplified)
        if age and 50 <= age <= 75:
            # no last visit within 10 years qualifies for colon cancer screening gap
            if not last_visit or (datetime.utcnow() - last_visit).days > 365 * 10:
                gaps.append("ColonCancer")
        # Mammogram (simplified)
        if d.get("gender") == "F" and age and 40 <= age <= 74:
            if not last_visit or (datetime.utcnow() - last_visit).days > 18 * 30:
                gaps.append("Mammogram")
        # Diabetes HbA1c
        if "E11" in diag:
            if not last_visit or (datetime.utcnow() - last_visit).days > 365:
                gaps.append("Diabetes-HbA1c")

        if gaps:
            flagged.append({
                "patient_id": d.get("patient_id"),
                "age": age,
                "gender": d.get("gender"),
                "gap_types": gaps,
                "last_visit": d.get("last_visit"),
                "contact": d.get("contact"),
            })

    return flagged


def main():
    print("Running care-gap identification aggregation...")
    flagged = find_care_gaps()
    print(f"Found {len(flagged)} patients with care gaps")
    # Print a brief summary
    for p in flagged[:20]:
        print(p["patient_id"], p["age"], p["gap_types"])

    # Call LangChain agent to prioritize and produce talking points
    outputs = prioritize_and_generate_talking_points(flagged)
    print("\nPrioritization / Talking Points:\n")
    print(json.dumps(outputs, default=str, indent=2))


if __name__ == "__main__":
    main()
