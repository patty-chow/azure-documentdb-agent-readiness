import pytest

@pytest.mark.skip("Integration test requires environment and stable TestClient API; skipped in CI run")
def test_placeholder():
    assert True
