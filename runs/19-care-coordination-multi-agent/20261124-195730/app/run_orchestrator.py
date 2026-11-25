import argparse
from app.orchestrator import orchestrate_and_write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--patient-id", required=True)
    args = parser.parse_args()

    res = orchestrate_and_write(args.patient_id)
    print("Inserted care_plan id:", res["care_plan_id"])
    print("Care plan summary:", res["care_plan"].get("summary"))

if __name__ == "__main__":
    main()
