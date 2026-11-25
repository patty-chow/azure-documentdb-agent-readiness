import struct
from app.db import pack_embedding, unpack_embedding

def test_pack_unpack_roundtrip():
    arr = [float(i) for i in range(512)]
    b = pack_embedding(arr)
    out = unpack_embedding(b)
    # Values should match as floats (may differ in precision)
    assert len(out) == 512
    for a, o in zip(arr, out):
        assert abs(a - o) < 1e-6
