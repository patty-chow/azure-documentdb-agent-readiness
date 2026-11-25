import os
import pytest

from src.db import DOCUMENTDB_URI


@pytest.mark.skipif(not DOCUMENTDB_URI, reason="DOCUMENTDB_URI not set in environment")
def test_seed_and_detect_runs():
    # This test verifies that seed and detector scripts can run against a real cluster.
    from src.seed_data import main as seed_main
    from src.run_detector import main as run_main
    # Call seed and run with a small limit to ensure queries execute
    seed_main()  # our seed_data.py uses top-level main style; in our file it's guarded by __main__ so import runs functions
    run_main(limit=5)
