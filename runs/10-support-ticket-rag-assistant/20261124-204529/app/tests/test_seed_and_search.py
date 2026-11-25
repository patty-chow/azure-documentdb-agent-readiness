import os
import subprocess
from dotenv import load_dotenv
load_dotenv()

def test_seed_runs():
    # run seed.py
    ret = subprocess.run(["python", "seed.py"], capture_output=True, text=True)
    assert ret.returncode == 0, ret.stderr


def test_verify_retrieval_runs():
    ret = subprocess.run(["python", "-m", "src.verify_retrieval"], capture_output=True, text=True)
    assert ret.returncode == 0, ret.stderr
    # output should include 'Query:'
    assert 'Query:' in ret.stdout
