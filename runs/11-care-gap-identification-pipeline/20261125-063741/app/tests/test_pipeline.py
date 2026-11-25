from src.pipeline import detect_gaps
from datetime import datetime, timedelta


def make_patient(age, gender='F', diagnoses=None, last_visit=None, pid='x'):
    dob = datetime.utcnow().replace(year=datetime.utcnow().year - age)
    return {"_id": pid, "name": "Test", "dob": dob, "gender": gender, "diagnoses": diagnoses or [], "last_visit_date": last_visit}


def test_detect_gaps_simple():
    # Patient age 60 female, no visits -> should trigger mammogram and colonoscopy
    p = make_patient(60, gender='F', diagnoses=[])
    res = detect_gaps([p])
    assert len(res) == 1
    gap_types = {g['gap_type'] for g in res[0]['gaps']}
    assert 'mammogram' in gap_types and 'colonoscopy' in gap_types


def test_detect_gaps_diabetes():
    # Patient with diabetes and recent visit -> may not trigger diabetic_hba1c if visit within 200 days
    recent = datetime.utcnow() - timedelta(days=100)
    p = make_patient(55, gender='M', diagnoses=['diabetes'], last_visit=recent)
    res = detect_gaps([p])
    # Diabetes interval is 365, so 100 days -> no gap
    assert len(res) == 0

    # Old visit
    old = datetime.utcnow() - timedelta(days=400)
    p2 = make_patient(55, gender='M', diagnoses=['diabetes'], last_visit=old)
    res2 = detect_gaps([p2])
    assert len(res2) == 1
    assert any(g['gap_type'] == 'diabetic_hba1c' for g in res2[0]['gaps'])
