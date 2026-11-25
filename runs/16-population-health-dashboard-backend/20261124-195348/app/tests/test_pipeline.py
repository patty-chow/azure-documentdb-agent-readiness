import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from aggregations import build_match_from_params, build_facet_pipeline


def test_build_match_simple():
    params = {"min_age": 30, "max_age": 50, "gender": "female,male", "region": "North,East", "diagnosis": "HTN"}
    match = build_match_from_params(params)
    assert "age" in match and "$gte" in match["age"] and "$lte" in match["age"]
    assert match["gender"]["$in"] == ["female", "male"]
    assert match["region"]["$in"] == ["North", "East"]
    assert match["diagnoses"]["$in"] == ["HTN"]


def test_build_facet_contains_facet():
    match = {"age": {"$gte": 20}}
    pipeline = build_facet_pipeline(match)
    assert any("$facet" in stage for stage in pipeline)
