import pytest
from unittest.mock import patch, MagicMock

from app.orchestrator import orchestrate_and_write


@patch("app.orchestrator.write_care_plan")
@patch("app.orchestrator.get_medications")
@patch("app.orchestrator.get_referrals")
@patch("app.orchestrator.get_patient_record")
def test_orchestrator_fallback(mock_patient, mock_referrals, mock_meds, mock_write):
    mock_patient.return_value = {"patient_id": "patient-001", "notes": "Test note"}
    mock_referrals.return_value = [{"note": "Refer to cardiology"}]
    mock_meds.return_value = [{"medication": "Aspirin"}]
    mock_write.return_value = "fake-id"

    res = orchestrate_and_write("patient-001")
    assert res["care_plan_id"] == "fake-id"
    assert "care_plan" in res
    assert isinstance(res["care_plan"], dict)
    assert "summary" in res["care_plan"] or "sections" in res["care_plan"]
