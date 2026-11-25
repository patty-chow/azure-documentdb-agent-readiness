import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent import review_correspondent
import json

if __name__ == '__main__':
    res = review_correspondent(correspondent_id="c1")
    print(json.dumps(res, indent=2))
