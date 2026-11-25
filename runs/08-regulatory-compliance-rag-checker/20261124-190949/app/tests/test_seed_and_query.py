import os
import pytest
from dotenv import load_dotenv
load_dotenv()

from src.db import get_db


def test_db_connection():
    db = get_db()
    assert db.name == os.environ.get("DB_NAME", "sample_fintech_08")


# The following tests expect seed.py to have been run in the live environment.

def test_collections_exist():
    db = get_db()
    assert "regulatory" in db.list_collection_names()
    assert "internal_policies" in db.list_collection_names()

