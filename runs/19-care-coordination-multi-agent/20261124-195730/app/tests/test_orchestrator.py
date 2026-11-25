import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import patch, MagicMock

# Ensure OPENAI_API_KEY is present for LangChain OpenAI wrapper during tests
os.environ.setdefault("OPENAI_API_KEY", "test-key")

@patch("app.orchestrator.insert_care_plan")
@patch("app.orchestrator.GPAgent")
@patch("app.orchestrator.SpecialistAgent")
@patch("app.orchestrator.PharmacyAgent")
@patch("app.orchestrator.LLMChain.run")
def test_orchestrator_saves_care_plan(mock_chain_run, mock_pharm_cls, mock_spec_cls, mock_gp_cls, mock_insert):
    # Import inside test so env var is present before module init
    from app.orchestrator import Orchestrator

    # Arrange: mock agents
    gp = MagicMock()
    gp.fetch.return_value = {"patient_id": "patient-001", "notes": "GP note", "records": []}
    mock_gp_cls.return_value = gp

    spec = MagicMock()
    spec.fetch.return_value = {"patient_id": "patient-001", "referrals": "Referral note", "records": []}
    mock_spec_cls.return_value = spec

    pharm = MagicMock()
    pharm.fetch.return_value = {"patient_id": "patient-001", "medications": ["Lisinopril 10mg"], "records": []}
    mock_pharm_cls.return_value = pharm

    # Mock chain to return deterministic text
    mock_chain_run.return_value = "SYNTHESISED PLAN"

    mock_insert.return_value = "fake-id"

    orch = Orchestrator()

    # Act
    res = orch.orchestrate("patient-001")

    # Assert
    assert res["inserted_id"] == "fake-id"
    assert "SYNTHESISED PLAN" in res["plan_text"] or res["plan_text"] == "SYNTHESISED PLAN"
