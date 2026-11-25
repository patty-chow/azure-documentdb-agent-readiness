"""Run the orchestration for a reporting period and print result.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from src.db import get_db
from src.orchestrator import Orchestrator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--period', required=True, help='Reporting period, e.g., 2023-Q4')
    args = parser.parse_args()

    db = get_db()
    orch = Orchestrator(db)
    result = orch.run(args.period)
    print('Run complete:', result)

if __name__ == '__main__':
    main()
