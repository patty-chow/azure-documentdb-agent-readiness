import pytest
from unittest.mock import MagicMock, patch
from src.orchestrator import Orchestrator

@patch('src.orchestrator.IngestAgent')
@patch('src.orchestrator.DedupAgent')
@patch('src.orchestrator.EnrichAgent')
def test_run_batch(mock_enrich, mock_dedup, mock_ingest):
    mock_ingest.return_value.ingest = MagicMock()
    mock_dedup.return_value.run_merging_pass = MagicMock()
    mock_enrich.return_value.run_enrichment_pass = MagicMock()

    orch = Orchestrator()
    run_id = orch.run_batch(incoming_records=[{'email':'x@example.com','name':'X'}])
    assert run_id is not None

