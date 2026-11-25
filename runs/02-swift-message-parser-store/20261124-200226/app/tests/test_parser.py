import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.parser import parse_swift

def test_parse_basic_mt103():
    raw = "{1:F01}{2:I103}{4:\n:20:ID1\n:32A:240101USD123,45\n:50K:/1\nA\n:59:/2\nB\n-}"
    p = parse_swift(raw)
    assert p['message_type'] == 'MT103'
    assert p['message_id'] == 'ID1'
    assert p['amount'] == 123.45
    assert p['currency'] == 'USD'


def test_parse_mt202():
    raw = "{1:F01}{2:I202}{4:\n:20:ID2\n:32A:240102EUR1000,00\n-}"
    p = parse_swift(raw)
    assert p['message_type'] == 'MT202'
    assert p['message_id'] == 'ID2'
    assert p['amount'] == 1000.0
    assert p['currency'] == 'EUR'
