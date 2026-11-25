import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mongomock
import pytest
from src.orchestrator import Orchestrator

@pytest.fixture
def fake_db():
    client = mongomock.MongoClient()
    db = client['sample_banking_04']
    # seed minimal data
    db.accounts.insert_one({'_id': 'ACC-1', 'name': 'TestCo', 'region': 'US'})
    db.transactions.insert_one({'_id': 'TX-1', 'account_id': 'ACC-1', 'date': '2023-12-15', 'amount': 100.0, 'currency':'USD', 'reporting_period':'2023-Q4'})
    return db

def test_orchestrator_runs(fake_db):
    orch = Orchestrator(fake_db)
    res = orch.run('2023-Q4')
    assert 'run_id' in res
    assert res['validation']['status'] == 'pass'
    assert res['out_path'].startswith('examples/filing_')
