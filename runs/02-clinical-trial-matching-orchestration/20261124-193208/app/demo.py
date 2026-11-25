from app.main import match_patient

sample_patient = {
    "age": 60,
    "conditions": ["hypertension"],
    "labs": {"creatinine": 1.0},
    "notes": "Patient with long history of hypertension and well-controlled on medication."
}

if __name__ == '__main__':
    results = match_patient(sample_patient)
    import json
    print(json.dumps(results, indent=2))
