from app.main import deterministic_eligibility_check


def test_eligibility_pass():
    trial = {"criteria": {"min_age": 18, "max_age": 70, "conditions": ["hypertension"], "labs": {}}}
    patient = {"age": 50, "conditions": ["hypertension"], "labs": {}}
    eligible, reason = deterministic_eligibility_check(trial, patient)
    assert eligible


def test_eligibility_fail_age():
    trial = {"criteria": {"min_age": 18, "max_age": 55, "conditions": ["hypertension"], "labs": {}}}
    patient = {"age": 60, "conditions": ["hypertension"], "labs": {}}
    eligible, reason = deterministic_eligibility_check(trial, patient)
    assert not eligible


def test_eligibility_missing_condition():
    trial = {"criteria": {"min_age": 18, "max_age": 70, "conditions": ["diabetes"], "labs": {}}}
    patient = {"age": 50, "conditions": ["hypertension"], "labs": {}}
    eligible, reason = deterministic_eligibility_check(trial, patient)
    assert not eligible
