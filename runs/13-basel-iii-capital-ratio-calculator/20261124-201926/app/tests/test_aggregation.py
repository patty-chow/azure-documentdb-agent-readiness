import os
import pytest
from tools.aggregation_tool import DocumentDBAggregationTool

@pytest.mark.skipif(not os.environ.get("DOCUMENTDB_URI"), reason="DOCUMENTDB_URI not set")
def test_aggregate_totals_runs():
    tool = DocumentDBAggregationTool()
    totals = tool.aggregate_totals()
    assert "total_rwa" in totals
    assert "total_cet1" in totals
    assert "total_capital" in totals
    # Should be numeric
    assert isinstance(totals["total_rwa"], (int, float))
