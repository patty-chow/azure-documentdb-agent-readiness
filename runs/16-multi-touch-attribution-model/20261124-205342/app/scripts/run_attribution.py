from src.db import get_db
from src.attribution import run_attribution_for_all


def main():
    db = get_db()
    summary = run_attribution_for_all(db)
    print(f"Processed {summary.get('processed')} customers")

if __name__ == "__main__":
    main()
