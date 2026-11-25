from src.pipeline import run_end_to_end
import json

if __name__ == '__main__':
    out = run_end_to_end()
    print(json.dumps(out, default=str, indent=2))
