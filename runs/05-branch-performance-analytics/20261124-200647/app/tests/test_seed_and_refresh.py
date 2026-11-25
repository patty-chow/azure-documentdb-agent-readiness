import os
import subprocess


def test_seed_and_refresh_runs():
    # Run seed and refresh scripts to ensure they execute without error (requires DOCUMENTDB_URI env var)
    env = os.environ.copy()
    ret = subprocess.run(["python", "scripts/seed.py"], env=env)
    assert ret.returncode == 0
    ret2 = subprocess.run(["python", "scripts/refresh_summaries.py"], env=env)
    assert ret2.returncode == 0
