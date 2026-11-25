import os
import sys
import argparse
# ensure src is importable when running as a script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.summarizer import summarize_transcript


def main():
    parser = argparse.ArgumentParser(description="Summarize a telehealth transcript and store it in DocumentDB")
    parser.add_argument("--patient-id", required=True)
    parser.add_argument("--transcript", required=True)
    args = parser.parse_args()

    doc = summarize_transcript(args.transcript, args.patient_id)
    print("Stored summary:")
    print(doc)

if __name__ == "__main__":
    main()
