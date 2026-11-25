from sentence_transformers import SentenceTransformer

# Load the embedding model once (global)
_model = None


def get_model(name="all-MiniLM-L6-v2"): 
    global _model
    if _model is None:
        _model = SentenceTransformer(name)
    return _model


def embed_text(text):
    model = get_model()
    vec = model.encode(text, normalize_embeddings=True)
    # return Python float list for storage
    return vec.tolist()


def embed_many(texts):
    model = get_model()
    vecs = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vecs]
