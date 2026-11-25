import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
from pydantic import ValidationError
from src.models import ProfileData


def test_profile_fields():
    p = ProfileData(name="Alice", emails=["a@example.com"]) 
    assert p.name == "Alice"
    assert isinstance(p.emails, list)
