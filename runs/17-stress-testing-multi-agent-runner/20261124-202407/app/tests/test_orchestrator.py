import pytest
from unittest.mock import MagicMock, patch
from src.main import compute_impact_pipeline


def test_compute_pipeline_basic():
    scenario = { 'rate_shift_bps': 100, 'fx_shift_pct': -0.02 }
    pipeline = compute_impact_pipeline(scenario)
    # Ensure pipeline includes project and group stages
    assert any('$project' in stage for stage in pipeline)
    assert any('$group' in stage for stage in pipeline)

@patch('src.main.get_db')
def test_run_persists_run(mock_get_db):
    fake_db = MagicMock()
    fake_positions = MagicMock()
    fake_positions.aggregate.return_value = iter([{ '_id': None, 'total_impact': 123.45, 'by_instrument': [] }])
    fake_db.__getitem__.side_effect = lambda name: fake_positions if name == 'positions' else MagicMock()
    mock_get_db.return_value = fake_db

    # Import here to use patched get_db
    from src.main import run_once
    run_once()
    # Ensure stress_runs.insert_one called
    assert fake_db['stress_runs'].insert_one.called
