from pymongo import ASCENDING
from pymongo.errors import OperationFailure

def create_vector_index(research_coll, embedding_field: str = "embedding", dims: int = 1536):
    """Create a DocumentDB vector index using the `cosmosSearchOptions` extension.
    This uses the MongoDB createIndexes command with an index spec that includes
    a cosmosSearchOptions object, as required by Azure DocumentDB.
    """
    # Index name
    idx_name = f"idx_vector_{embedding_field}"
    idx_spec = {
        "key": {embedding_field: "cosmosSearch"},
        "name": idx_name,
        "background": True,
        "cosmosSearchOptions": {
            "kind": "vector-hnsw",
            "similarity": "COS",
            "dimensions": dims,
            # HNSW tuning defaults for small demo
            "m": 16,
            "efConstruction": 200
        }
    }
    try:
        # createIndexes via PyMongo helper
        research_coll.create_index([(embedding_field, "cosmosSearch")], name=idx_name)
        # Some clusters expect the options to be passed using command; if so, fall back
    except OperationFailure:
        # Fallback to database command
        research_coll.database.command({
            "createIndexes": research_coll.name,
            "indexes": [idx_spec]
        })
