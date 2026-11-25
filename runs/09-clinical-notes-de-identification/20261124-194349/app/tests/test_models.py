from src.models import RawNote, DeidNote


def test_model_names():
    assert RawNote.Settings.name == 'raw_notes'
    assert DeidNote.Settings.name == 'deid_notes'


def test_model_fields():
    # ensure expected annotations exist on the classes
    assert 'text' in RawNote.__annotations__
    assert 'sourceId' in DeidNote.__annotations__
