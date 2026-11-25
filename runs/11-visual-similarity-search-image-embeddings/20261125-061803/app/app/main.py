import io
import os
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import numpy as np
from .db import get_client, DB_NAME, COLLECTION_NAME, pack_embedding, unpack_embedding, ensure_vector_index, fetch_all_products
from .encoder import encode_image_pil, encode_image_fallback, load_model

logger = logging.getLogger("uvicorn.error")
app = FastAPI(title="DocumentDB Visual Similarity Search Sample")

# Attempt to lazily load model on startup if available
@app.on_event("startup")
def startup_event():
    try:
        load_model()
        logger.info("CLIP model loaded on startup")
    except Exception as ex:
        logger.warning("CLIP model not loaded: %s", ex)


@app.post("/visual-search")
async def visual_search(image: UploadFile = File(...)):
    try:
        contents = await image.read()
        pil = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"Invalid image upload: {ex}")

    # Try to encode with real model; fallback if unavailable
    try:
        vec = encode_image_pil(pil)
    except Exception:
        vec = encode_image_fallback(pil)

    # Connect to DB
    try:
        client = get_client()
        db = client[DB_NAME]
        coll = db[COLLECTION_NAME]
    except Exception as ex:
        # If no DB, perform client-side stub search over local files (not implemented)
        logger.warning("Could not connect to DB: %s", ex)
        raise HTTPException(status_code=500, detail="Could not connect to DocumentDB cluster; set DOCUMENTDB_URI")

    # Attempt server-side vector search (best-effort). If unsupported, fall back to fetching all embeddings and compute similarity locally.
    try:
        # Try an aggregation stage that some servers support for vector knn. This syntax varies across providers.
        pipeline = [
            {"$vectorSearch": {"knnBeta": {"vector": vec, "path": "embedding", "k": 8}}},
            {"$project": {"name": 1, "image_path": 1, "score": {"$meta": "searchScore"}}}
        ]
        docs = list(coll.aggregate(pipeline))
        # If we got results, return them
        if docs:
            return JSONResponse(content={"matches": docs})
    except Exception as ex:
        logger.info("Server-side vector search aggregation unavailable: %s", ex)

    # Fallback: fetch all embeddings and compute cosine similarity locally
    docs = fetch_all_products(db)
    if not docs:
        return JSONResponse(content={"matches": []})

    # Unpack embeddings and compute dot product
    import math
    q = np.array(vec, dtype="float32")
    results = []
    for d in docs:
        if "embedding" not in d:
            continue
        try:
            emb = np.array(unpack_embedding(d["embedding"]), dtype="float32")
            # cosine similarity since embeddings are normalized
            score = float(np.dot(q, emb) / (np.linalg.norm(q) * (np.linalg.norm(emb) + 1e-9)))
        except Exception:
            continue
        results.append({"_id": str(d.get("_id")), "name": d.get("name"), "image_path": d.get("image_path"), "score": score})
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:8]
    return JSONResponse(content={"matches": results})
