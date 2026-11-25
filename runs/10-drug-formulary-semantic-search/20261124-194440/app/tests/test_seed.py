import os
import subprocess

def test_seed_runs():
    # This integration test expects OPENAI_API_KEY and DOCUMENTDB_URI to be set in the environment
    # It will run the seed script which performs upserts.
    env = os.environ.copy()
    if 'OPENAI_API_KEY' not in env or 'DOCUMENTDB_URI' not in env:
        print('Skipping integration test: set OPENAI_API_KEY and DOCUMENTDB_URI to run')
        return
    res = subprocess.run(["python","scripts/seed_data.py"], capture_output=True, text=True)
    assert res.returncode == 0, f"Seed script failed: {res.stdout}\n{res.stderr}"
