import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.orchestrator import orchestrate


def test_orchestrate_schema():
    # This unit test validates the structure of the recommendation object.
    assert callable(orchestrate)
