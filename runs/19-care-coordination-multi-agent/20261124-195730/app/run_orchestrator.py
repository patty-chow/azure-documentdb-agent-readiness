import argparse
from app.orchestrator import Orchestrator

parser = argparse.ArgumentParser()
parser.add_argument("--patient-id", required=True)
args = parser.parse_args()

orch = Orchestrator()
res = orch.orchestrate(args.patient_id)
print("Inserted care plan id:", res.get("inserted_id"))
print("Plan summary:\n", res.get("plan_text"))
