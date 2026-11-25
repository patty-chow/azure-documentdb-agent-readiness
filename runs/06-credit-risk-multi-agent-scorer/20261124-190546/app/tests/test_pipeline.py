import sys
import os
# Ensure project root is on sys.path for pytest in this runner
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sample_fintech_06 import seed
from sample_fintech_06.run import run_pipeline
from sample_fintech_06.db import get_db


def test_pipeline_mock_end_to_end():
    # Ensure sample data exists
    seed.main()
    # Run pipeline in mock mode for applicant-1
    res = run_pipeline("applicant-1", use_llm=False, mock=True)
    assert res["applicant_id"] == "applicant-1"
    assert "score" in res and "final_score" in res["score"]

    # Verify DB updated
    db = get_db()
    doc = db.applicants.find_one({"_id": "applicant-1"})
    assert doc is not None
    assert "creditScore" in doc
    assert "creditScoreExplanation" in doc

