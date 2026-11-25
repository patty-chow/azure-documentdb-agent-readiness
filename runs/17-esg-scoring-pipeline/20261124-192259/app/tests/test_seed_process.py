import os
import pytest
from unittest.mock import patch, MagicMock

import sample.seed as seed_mod
import sample.process as process_mod


@patch("sample.seed.get_db")
def test_seed_creates_indexes_and_upserts(get_db_mock):
    # Mock collection
    col = MagicMock()
    get_db_mock.return_value = {"esg_companies": col}
    # run seed
    seed_mod.seed()
    # check index creation called
    assert col.create_index.call_count >= 1
    assert col.update_one.call_count >= 1


@patch("sample.process.get_db")
def test_process_fallback(get_db_mock):
    # Provide a collection with one doc missing scores
    doc = {"_id": 1, "raw_esg_text": "Test text"}
    col = MagicMock()
    col.find.return_value = [doc]
    col.bulk_write.return_value = MagicMock(matched_count=1, modified_count=1)
    get_db_mock.return_value = {"esg_companies": col}
    process_mod.process_all()
    # ensure bulk_write called
    assert col.bulk_write.called
