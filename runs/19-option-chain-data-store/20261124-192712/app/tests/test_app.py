import os
import importlib


def test_files_exist():
    assert os.path.exists('app/db.py')
    assert os.path.exists('app/main.py')
    assert os.path.exists('scripts/ensure_indexes.py')
    assert os.path.exists('scripts/seed.py')
    assert os.path.exists('seeds/sample_chain.json')


def test_db_module_has_get_db():
    mod = importlib.import_module('app.db')
    assert hasattr(mod, 'get_db')
    assert callable(mod.get_db)
