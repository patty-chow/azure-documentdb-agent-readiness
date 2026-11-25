import sys
from pathlib import Path

# Ensure the repository root is on PYTHONPATH so tests can import src
ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
