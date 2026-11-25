import pytest
from src.agents import ScenarioAgent, ReportingAgent


def test_scenario_agent():
    agent = ScenarioAgent(seed=42)
    s = agent.generate()
    assert "rate_bps" in s
    assert "fx_shocks" in s


def test_reporting_agent_without_llm():
    scenario = {"id": "scenario_test", "rate_bps": 100, "fx_shocks": {"USD": 0}, "created_at": 0}
    impact = {"total_pl": 12345.6, "per_instrument": [{"_id": {"instrument": "BOND_US_10Y"}, "instrument_pl": 12345.6}], "count_instruments": 1}
    reporter = ReportingAgent(llm_client=None)
    report = reporter.synthesize(scenario, impact)
    assert report["scenario"]["id"] == "scenario_test"
    assert "impact_summary" in report
    assert report["impact_summary"]["total_pl"] == 12345.6
