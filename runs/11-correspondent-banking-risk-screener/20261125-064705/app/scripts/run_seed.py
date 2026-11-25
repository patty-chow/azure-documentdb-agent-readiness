import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.seed import ensure_and_seed

if __name__ == '__main__':
    ensure_and_seed()
