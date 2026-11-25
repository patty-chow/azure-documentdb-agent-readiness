from src.agent import format_system_prompt, format_user_prompt


def test_system_prompt_contains_scenarios():
    sp = format_system_prompt()
    assert "Parallel shift" in sp or "parallel shift" in sp.lower()


def test_user_prompt_includes_json():
    agg = [{"bucket": "0-1y", "rate_type": "fixed", "notional": 1000000, "count": 2, "avg_coupon": 0.02}]
    up = format_user_prompt(agg)
    assert "0-1y" in up
    assert "notional" in up
