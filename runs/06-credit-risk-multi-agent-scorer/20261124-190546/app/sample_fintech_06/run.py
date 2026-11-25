"""CLI runner for the pipeline."""
import argparse
from .agents import fetch_applicant, score_applicant, explain_score
from .db import get_db


def run_pipeline(applicant_id: str, use_llm: bool = False, mock: bool = False):
    applicant = fetch_applicant(applicant_id)
    score = score_applicant(applicant, use_llm=use_llm, mock=mock)
    explanation = explain_score(applicant, score, use_llm=use_llm, mock=mock)

    # write back
    db = get_db()
    update = {
        "$set": {
            "creditScore": score["final_score"],
            "creditScoreDetails": score["details"],
            "creditScoreExplanation": explanation,
        }
    }
    db.applicants.update_one({"_id": applicant_id}, update)
    return {"applicant_id": applicant_id, "score": score, "explanation": explanation}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--applicant-id", required=True)
    parser.add_argument("--mock", action="store_true", help="Use mock LLM responses")
    parser.add_argument("--use-llm", action="store_true", help="Attempt real LLM calls (requires OPENAI_API_KEY)")
    args = parser.parse_args()
    out = run_pipeline(args.applicant_id, use_llm=args.use_llm, mock=args.mock)
    print(out)
