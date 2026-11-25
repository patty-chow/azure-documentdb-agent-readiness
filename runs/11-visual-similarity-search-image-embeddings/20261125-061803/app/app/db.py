import os
import struct
import logging
from bson.binary import Binary
from pymongo import MongoClient
from typing import List

logger = logging.getLogger(__name__)

DB_NAME = "sample_retail_11"
COLLECTION_NAME = "products"

def get_client():
    uri = os.environ.get("DOCUMENTDB_URI")
    if not uri:
        raise RuntimeError("DOCUMENTDB_URI environment variable is required to connect to DocumentDB")
    return MongoClient(uri)

def pack_embedding(array) -> Binary:
    """Pack a sequence of float32 into BSON Binary subtype 0x09 (little-endian)."""
    # Use struct to pack as little-endian float32
    b = struct.pack("<%sf" % (len(array),), *[float(x) for x in array])
    return Binary(b, subtype=0x09)

def unpack_embedding(bin_data: Binary) -> List[float]:
    b = bytes(bin_data)
    count = len(b) // 4
    vals = struct.unpack("<%sf" % count, b)
    return list(vals)


def ensure_vector_index(db):
    """Attempt to create a vector-ivf index on the embedding field with plausible options.
    If the server rejects the options, log the failure; exact option names vary by server.
    """
    coll = db[COLLECTION_NAME]
    try:
        # Many MongoDB-compatible vector implementations accept a special index type or options.
        # We attempt a plausible create_index and rely on server error messages if unsupported.
        index_name = "embedding_vector_ivf"
        index_spec = [("embedding", "vector")]
        index_options = {
            "name": index_name,
            # These option names are plausible; servers may require different keys.
            "vectorIndexType": "ivf",
            "dimensions": 512,
            "metric": "cosine",
            "indexOptions": {"nlist": 100},
        }
        coll.create_index(index_spec, **index_options)
        logger.info("Requested creation of vector index %s", index_name)
    except Exception as ex:
        logger.warning("Creating vector index failed or is unsupported on server: %s", ex)
        # Don't re-raise; sample should continue and fall back to client-side search if needed.

def fetch_all_products(db):
    coll = db[COLLECTION_NAME]
    docs = list(coll.find({}, {"embedding": 1, "name": 1, "image_path": 1}))
    return docs
