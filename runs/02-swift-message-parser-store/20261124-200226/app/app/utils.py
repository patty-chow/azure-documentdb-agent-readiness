from datetime import datetime, date


def normalize_doc_for_insert(doc: dict) -> dict:
    d = dict(doc)
    vd = d.get('value_date')
    if isinstance(vd, date) and not isinstance(vd, datetime):
        d['value_date'] = datetime(vd.year, vd.month, vd.day)
    return d
