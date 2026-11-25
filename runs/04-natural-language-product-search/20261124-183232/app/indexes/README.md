Index templates for Azure DocumentDB

This folder contains templates and instructions to create the BM25 full-text search index and a vector index for the `products` collection in database `sample_retail_04`.

Follow the Microsoft Learn guidance to apply these templates using `mongosh` or the portal. The sample app expects a search index named `default-search-index` and a vector index named `default-vector-index`.

Files:
- search_index.json - template for createSearchIndexes command (BM25 over title and description)
- vector_index.json - template for vector index definition (cosmosSearch vector-hnsw / diskann depending on scale)

IMPORTANT: Do not post your connection string or keys. Use mongosh with your DOCUMENTDB_URI to run the commands:

Example (mongosh):
> use sample_retail_04
> db.runCommand({ createSearchIndexes: "products", indexes: [ <contents-of-search_index.json> ] })

For the vector index, refer to Learn docs and pick the appropriate `kind` (vector-hnsw, vector-ivf, vector-diskann).
