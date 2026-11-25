import struct
import numpy as np
from bson.binary import Binary


def floats_to_bsonbinary(floats):
    # pack as float32 little-endian
    arr = np.asarray(floats, dtype=np.float32)
    return Binary(arr.tobytes())


def bsonbinary_to_floats(binary, dims=None):
    # binary is bson.Binary containing float32 bytes
    b = bytes(binary)
    # infer dims
    if dims is None:
        dims = len(b) // 4
    arr = np.frombuffer(b, dtype=np.float32, count=dims)
    return arr.tolist()
