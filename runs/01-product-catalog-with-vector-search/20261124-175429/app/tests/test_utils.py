import struct
import numpy as np
from app import normalize, pack_embedding, unpack_embedding


def test_normalize():
    v = np.array([3.0, 4.0], dtype=np.float32)
    n = normalize(v)
    assert abs(np.linalg.norm(n) - 1.0) < 1e-6


def test_pack_unpack():
    v = np.random.RandomState(0).randn(10).astype('float32')
    packed = pack_embedding(v)
    unpacked = unpack_embedding(packed)
    assert len(unpacked) == 10
    # compare floats with tolerance
    for a, b in zip(unpacked, v.tolist()):
        assert abs(a - b) < 1e-6
