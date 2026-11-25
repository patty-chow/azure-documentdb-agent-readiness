import io
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import bson
import torch

from .db import get_db

from transformers import CLIPProcessor, CLIPModel

app = FastAPI()

# Load model once
model_name = "openai/clip-vit-base-patch32"
processor = CLIPProcessor.from_pretrained(model_name)
model = CLIPModel.from_pretrained(model_name)

# normalize to unit length for cosine similarity

def image_to_embedding(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = processor(images=img, return_tensors="pt")
    with torch.no_grad():
        features = model.get_image_features(**inputs)
    vec = features[0].cpu().numpy()
    # normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.astype(np.float32)

@app.post("/visual-search")
async def visual_search(file: UploadFile = File(...)):
    data = await file.read()
    try:
        qvec = image_to_embedding(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image or encoding error: {e}")

    # store as bson binary subtype 0x09 as required
    qb = bson.Binary(qvec.tobytes(), subtype=0x09)

    db = get_db()
    coll = db["products"]

    # Query vector should be an array of floats
    qlist = qvec.tolist()

    # Build $search aggregation stage for cosmosSearch vector query
    search_stage = {
        "$search": {
            "cosmosSearch": {
                "path": "embedding",
                "vector": qlist,
                "k": 8,
                "cosmosSearchOptions": {
                    "kind": "vector-ivf",
                    "dimensions": 512,
                    "similarity": "COS"
                }
            }
        }
    }

    pipeline = [search_stage,
        {"$project": {"name": 1, "image_url": 1, "score": {"$meta": "searchScore"}}},
        {"$limit": 8}
    ]

    try:
        # use database command for aggregate to ensure $search is initial
        res = db.command({"aggregate": "products", "pipeline": pipeline, "cursor": {}})
        results = res.get('cursor', {}).get('firstBatch', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search query failed: {e}")

    # Convert ObjectId to string
    for r in results:
        if "_id" in r:
            r["_id"] = str(r["_id"])
    return JSONResponse(content={"results": results})
