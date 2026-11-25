"""Run a quick local demo of the client-side fallback visual search using the seeded data."""
from PIL import Image
from app.encoder import encode_image_fallback
from app.db import get_client, DB_NAME, fetch_all_products, unpack_embedding
import numpy as np

img_path = "sample_data/product_0.jpg"
img = Image.open(img_path).convert("RGB")
vec = encode_image_fallback(img)
client = get_client()
db = client[DB_NAME]
docs = fetch_all_products(db)
q = np.array(vec, dtype="float32")
results = []
for d in docs:
    if "embedding" not in d:
        continue
    emb = np.array(unpack_embedding(d["embedding"]), dtype="float32")
    score = float(np.dot(q, emb) / (np.linalg.norm(q) * (np.linalg.norm(emb) + 1e-9)))
    results.append({"name": d.get("name"), "image_path": d.get("image_path"), "score": score})
results = sorted(results, key=lambda x: x["score"], reverse=True)[:8]
print(results)
